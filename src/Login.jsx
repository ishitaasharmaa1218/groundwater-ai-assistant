import { useState } from "react"
import axios from "axios"

export default function Login({setUser}){

const [email,setEmail] = useState("")
const [password,setPassword] = useState("")

async function login(){

const res = await axios.post(
"http://127.0.0.1:8000/login",
null,
{params:{email,password}}
)

localStorage.setItem("token",res.data.token)
localStorage.setItem("user_id",res.data.user_id)

setUser(res.data.user_id)
}

return(

<div className="login">

<h2>Login</h2>

<input placeholder="Email" onChange={e=>setEmail(e.target.value)}/>
<input placeholder="Password" type="password"
onChange={e=>setPassword(e.target.value)}/>

<button onClick={login}>Login</button>

</div>

)

}