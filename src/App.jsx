body{
margin:0;
font-family:Arial;
background:#eef7ff;
}

.app{
display:flex;
height:100vh;
}

/* Sidebar */

.sidebar{
width:260px;
background:#0b5fa5;
color:white;
padding:20px;
overflow:auto;
}

.sidebar h2{
margin-bottom:20px;
}

.history{
background:#1976d2;
padding:10px;
margin-bottom:10px;
border-radius:6px;
cursor:pointer;
}

/* Chat */

.chat{
flex:1;
display:flex;
flex-direction:column;
}

.messages{
flex:1;
padding:30px;
overflow:auto;
}

.user{
background:#1976d2;
color:white;
padding:12px;
border-radius:10px;
max-width:60%;
margin-bottom:12px;
margin-left:auto;
}

.assistant{
background:white;
border:1px solid #d0e4ff;
padding:12px;
border-radius:10px;
max-width:60%;
margin-bottom:12px;
}

/* Input */

.inputArea{
display:flex;
padding:20px;
border-top:1px solid #ddd;
}

input{
flex:1;
padding:12px;
font-size:16px;
border:1px solid #ccc;
border-radius:6px;
}

button{
margin-left:10px;
padding:12px 20px;
background:#0b5fa5;
color:white;
border:none;
border-radius:6px;
cursor:pointer;
}

button:hover{
background:#084a83;
}