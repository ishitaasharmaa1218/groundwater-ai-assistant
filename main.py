import math
from fastapi import FastAPI
import psycopg2
from fastapi.responses import StreamingResponse
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import io
import difflib

import joblib
model = joblib.load("groundwater_model.pkl")

from dotenv import load_dotenv
load_dotenv()

from openai import OpenAI
client = OpenAI()

from fastapi.middleware.cors import CORSMiddleware

from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException

app = FastAPI()

# ------------------ CORS ------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------ DB CONNECTION ------------------

conn = psycopg2.connect(
    database="groundwater_db",
    user="postgres",
    password="postgre123",
    host="localhost",
    port="5432"
)

# ------------------ AUTH SETUP ------------------

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = "groundwater_secret_key"
ALGORITHM = "HS256"

def hash_password(password):
    return pwd_context.hash(password)

def verify_password(password, hashed):
    return pwd_context.verify(password, hashed)

def create_token(data):
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=12)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

# ------------------ HOME ------------------

@app.get("/")
def home():
    return {"message": "Groundwater AI API running"}

# ------------------ SIGNUP ------------------

@app.post("/signup")
def signup(username:str,email:str,password:str):

    cursor = conn.cursor()

    hashed = hash_password(password)

    try:
        cursor.execute(
        "INSERT INTO users(username,email,password_hash) VALUES(%s,%s,%s)",
        (username,email,hashed)
        )
        conn.commit()

    except:
        raise HTTPException(status_code=400,detail="User already exists")

    return {"message":"Signup successful"}

# ------------------ LOGIN ------------------

@app.post("/login")
def login(email:str,password:str):

    cursor = conn.cursor()

    cursor.execute(
    "SELECT id,password_hash FROM users WHERE email=%s",
    (email,)
    )

    user = cursor.fetchone()

    if not user:
        raise HTTPException(status_code=401,detail="User not found")

    if not verify_password(password,user[1]):
        raise HTTPException(status_code=401,detail="Wrong password")

    token = create_token({"user_id":user[0]})

    return {"token":token,"user_id":user[0]}

# ------------------ GET USER HISTORY ------------------

@app.get("/history/{user_id}")
def get_history(user_id:int):

    cursor = conn.cursor()

    cursor.execute(
    "SELECT question,answer FROM chat_history WHERE user_id=%s ORDER BY created_at DESC",
    (user_id,)
    )

    rows = cursor.fetchall()

    history = []

    for r in rows:
        history.append({
            "question": r[0],
            "answer": r[1]
        })

    return {"history":history}

# ------------------ DISTRICT SPELLCHECK ------------------

known_districts = []
try:
    _cursor = conn.cursor()
    _cursor.execute("SELECT DISTINCT district FROM groundwater_resources")
    known_districts = [r[0].lower() for r in _cursor.fetchall() if r[0]]
    _cursor.close()
except Exception:
    pass

known_keywords = ["risk","trend","summary","status","level","predict","future"]
all_known_words = known_keywords + known_districts

# ------------------ DATA APIs ------------------

@app.get("/groundwater/{district}")
def get_groundwater(district: str):

    cursor = conn.cursor()

    query = """
    SELECT block, annual_recharge, net_groundwater,
           groundwater_development_percent
    FROM groundwater_resources
    WHERE district ILIKE %s
    """

    cursor.execute(query,(f"%{district}%",))
    rows = cursor.fetchall()

    result = []

    for r in rows:
        cleaned_row = tuple(
            None if isinstance(x,float) and math.isnan(x) else x
            for x in r
        )

        result.append({
            "block": cleaned_row[0],
            "annual_recharge": cleaned_row[1],
            "net_groundwater": cleaned_row[2],
            "groundwater_development_percent": cleaned_row[3]
        })

    cursor.close()

    return {"district":district,"data":result}

# ------------------ SUMMARY ------------------

@app.get("/summary/{district}")
def groundwater_summary(district:str):

    cursor = conn.cursor()

    query="""
    SELECT 
        AVG(annual_recharge),
        AVG(net_groundwater),
        AVG(groundwater_development_percent)
    FROM groundwater_resources
    WHERE district ILIKE %s
    """

    cursor.execute(query,(f"%{district}%",))
    row=cursor.fetchone()
    cursor.close()

    cleaned_row = tuple(
        None if isinstance(x,float) and math.isnan(x) else x
        for x in row
    )

    return {
        "district":district,
        "data":{
            "avg_annual_recharge":cleaned_row[0],
            "avg_net_groundwater":cleaned_row[1],
            "avg_groundwater_development":cleaned_row[2]
        }
    }

# ------------------ RISK ------------------

@app.get("/risk/{district}")
def groundwater_risk(district:str):

    cursor=conn.cursor()

    query="""
    SELECT block, groundwater_development_percent
    FROM groundwater_resources
    WHERE district ILIKE %s
    """

    cursor.execute(query,(f"%{district}%",))
    rows=cursor.fetchall()

    risk_blocks=[]

    for r in rows:

        percent=r[1]

        if percent is None or (isinstance(percent,float) and math.isnan(percent)):
            continue

        if percent>90:
            risk="OVEREXPLOITED"
        elif percent>70:
            risk="CRITICAL"
        else:
            risk="SAFE"

        risk_blocks.append({
            "block":r[0],
            "risk":risk,
            "groundwater_development_percent":percent
        })

    cursor.close()

    return {"district":district,"data":risk_blocks}

# ------------------ TREND ------------------

@app.get("/trend/{district}")
def groundwater_trend(district:str):

    cursor=conn.cursor()

    query="""
    SELECT block, annual_recharge, net_groundwater
    FROM groundwater_resources
    WHERE district ILIKE %s
    """

    cursor.execute(query,(f"%{district}%",))
    rows=cursor.fetchall()
    cursor.close()

    trend_data=[]

    for r in rows:

        recharge=r[1]
        groundwater=r[2]

        if recharge is None or groundwater is None:
            continue

        if isinstance(recharge,float) and math.isnan(recharge):
            continue

        if isinstance(groundwater,float) and math.isnan(groundwater):
            continue

        if recharge>groundwater:
            trend="RECHARGING"
        elif groundwater>recharge:
            trend="DECLINING"
        else:
            trend="STABLE"

        trend_data.append({
            "block":r[0],
            "annual_recharge":recharge,
            "net_groundwater":groundwater,
            "trend":trend
        })

    return {"district":district,"data":trend_data}

# ------------------ PREDICTION ------------------

@app.get("/predict/{district}")
def groundwater_prediction(district:str):

    cursor=conn.cursor()

    query="""
    SELECT AVG(annual_recharge)
    FROM groundwater_resources
    WHERE district ILIKE %s
    """

    cursor.execute(query,(f"%{district}%",))
    row=cursor.fetchone()
    cursor.close()

    recharge=row[0] if row else None

    if recharge is None:
        return {"district":district,"predicted_net_groundwater":None}

    prediction=model.predict([[recharge]])

    return {
        "district":district,
        "predicted_net_groundwater":float(prediction[0]),
        "based_on_recharge":recharge
    }

# ------------------ CHARTS ------------------

@app.get("/chart/trend/{district}")
def get_trend_chart(district:str):
    cursor=conn.cursor()
    query="""
    SELECT block, annual_recharge, net_groundwater
    FROM groundwater_resources
    WHERE district ILIKE %s
    """
    cursor.execute(query,(f"%{district}%",))
    rows=cursor.fetchall()
    cursor.close()

    blocks, recharge, net = [], [], []
    for r in rows:
        if r[1] is None or r[2] is None: continue
        if isinstance(r[1],float) and math.isnan(r[1]): continue
        if isinstance(r[2],float) and math.isnan(r[2]): continue
        blocks.append(str(r[0])[:12])
        recharge.append(r[1])
        net.append(r[2])

    if not blocks:
        raise HTTPException(status_code=404, detail="No data")

    plt.figure(figsize=(10,5))
    x = range(len(blocks))
    plt.bar(x, recharge, width=0.4, label='Annual Recharge', color='#3b82f6')
    plt.bar([p + 0.4 for p in x], net, width=0.4, label='Net Groundwater', color='#10b981')
    plt.xticks([p + 0.2 for p in x], blocks, rotation=45, ha='right')
    plt.title(f"Groundwater Data - {district.title()}")
    plt.ylabel('Units')
    plt.legend()
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    plt.close()

    return StreamingResponse(buf, media_type="image/png")

# ------------------ AI ASSISTANT ------------------

@app.get("/ask")
def groundwater_ai(question:str,user_id:int=None):

    q=question.lower().strip()
    words=q.split()

    corrected_words=[]

    for w in words:
        matches=difflib.get_close_matches(w,all_known_words,n=1,cutoff=0.7)
        corrected_words.append(matches[0] if matches else w)

    q=" ".join(corrected_words)

    if "risk" in q:
        district=q.split()[-1]
        data=groundwater_risk(district)

    elif "trend" in q:
        district=q.split()[-1]
        data=groundwater_trend(district)

    elif "summary" in q or "status" in q or "level" in q:
        district=q.split()[-1]
        data=groundwater_summary(district)

    elif "predict" in q or "future" in q:
        district=q.split()[-1]
        data=groundwater_prediction(district)

    else:
        return {"answer":"Ask about groundwater risk, trend, summary, level or prediction."}

    # Check if data is empty
    has_data = False
    if "predicted_net_groundwater" in data:
        if data.get("based_on_recharge") is not None:
            has_data = True
    else:
        inner = data.get("data")
        if isinstance(inner, list) and len(inner) > 0:
            has_data = True
        elif isinstance(inner, dict) and inner.get("avg_annual_recharge") is not None:
            has_data = True

    if not has_data:
        return {
            "answer": "The working of model is still in progress. The data of this district is still not trained. Thank you!"
        }

    # Determine if a visualization should be attached
    chart_url = None
    if any(k in q for k in ["trend", "risk", "level", "summary"]):
        chart_url = f"http://127.0.0.1:8000/chart/trend/{district}"

    try:
        response=client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role":"system","content":"You are a groundwater expert."},
                {"role":"user","content":f"Question:{question}\nData:{data}\nExplain."}
            ]
        )
        answer=response.choices[0].message.content
    except Exception as e:
        # Fallback to a detailed rule-based intelligent summary since OpenAI is unavailable
        try:
            if "risk" in q:
                blocks = data.get("data", [])
                safe = sum(1 for b in blocks if b.get('risk') == 'SAFE')
                critical = sum(1 for b in blocks if b.get('risk') == 'CRITICAL')
                overexploited = sum(1 for b in blocks if b.get('risk') == 'OVEREXPLOITED')
                answer = (f"Hello! I have analyzed the groundwater risk profile for the {district.title()} district. "
                          f"Out of the {len(blocks)} blocks evaluated, {safe} are currently classified as 'SAFE'. "
                          f"However, there is cause for attention: {critical} blocks are 'CRITICAL' and {overexploited} are 'OVEREXPLOITED', meaning water extraction heavily exceeds natural recharge. "
                          f"Immediate water conservation methods and strict pumping regulations should be prioritized in these vulnerable regions to prevent severe aquifer depletion.")
            elif "trend" in q:
                blocks = data.get("data", [])
                recharging = sum(1 for b in blocks if b.get('trend') == 'RECHARGING')
                declining = sum(1 for b in blocks if b.get('trend') == 'DECLINING')
                answer = (f"I have reviewed the multi-year groundwater trend data for {district.title()}. "
                          f"The situation presents a mixed picture. On the positive side, {recharging} blocks are showing a 'RECHARGING' trend, meaning their aquifers are gradually recovering. "
                          f"Conversely, {declining} blocks are actively 'DECLINING'. This indicates an urgent need for artificial recharge structures like check dams and percolation tanks in the declining zones to reverse the downward trend.")
            elif "summary" in q or "status" in q or "level" in q:
                avg_r = data.get("data", {}).get("avg_annual_recharge", 0)
                avg_net = data.get("data", {}).get("avg_net_groundwater", 0)
                answer = (f"Here is your comprehensive groundwater summary for {district.title()}. "
                          f"The region has an average annual groundwater recharge potential of {avg_r:.2f} units, against an average net groundwater level of {avg_net:.2f} units. "
                          f"This balance highlights the overall dynamic stability of the local aquifer system. Maintaining this balance is crucial for ensuring long-term agricultural and domestic water security.")
            elif "predict" in q or "future" in q:
                pred = data.get("predicted_net_groundwater", 0)
                basis = data.get("based_on_recharge", 0)
                answer = (f"Using our predictive machine learning models, I've forecasted the future groundwater index for {district.title()}. "
                          f"Given the current baseline average recharge of {basis:.2f} units, the model projects that net groundwater availability will stabilize at approximately {pred:.2f} units. "
                          f"Continuous monitoring and optimized irrigation practices will be necessary to meet or exceed these forecasts.")
            else:
                answer = f"Data successfully retrieved and processed for the {district.title()} district."
                
            answer += "\n\n**Source:** Central Ground Water Board (CGWB) & India WRIS Database."
        except Exception as inner_e:
            answer = "Data retrieved successfully, but a detailed human-readable summary could not be generated."

    # -------- SAVE CHAT HISTORY --------

    if user_id is not None:
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE id=%s", (user_id,))
        if cursor.fetchone():
            cursor.execute(
                "INSERT INTO chat_history(user_id,question,answer) VALUES(%s,%s,%s)",
                (user_id,question,answer)
            )
            conn.commit()
        cursor.close()

    return {
        "question":question,
        "answer":answer,
        "chartUrl": chart_url,
        "data":data
    }

# ------------------ SERVER ------------------

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app,host="127.0.0.1",port=8000)