function tog(id){document.getElementById('r-'+id).classList.toggle('open')}
function tick(){const d=new Date();document.getElementById('clk').textContent=[d.getHours(),d.getMinutes(),d.getSeconds()].map(n=>String(n).padStart(2,'0')).join(':')}
setInterval(tick,1000);tick()

function ck(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sc()}}
function addBubble(role, text){
  const msgs = document.getElementById('cmsgs')
  const row = document.createElement('div')
  row.className = 'bubble-row'
  const label = document.createElement('div')
  label.className = 'bubble-label'
  const bubble = document.createElement('div')
  bubble.className = 'bubble ' + (role === 'ct' ? 'ct' : 'user')
  const d = new Date()
  const ts = [d.getHours(), d.getMinutes()].map(n => String(n).padStart(2, '0')).join(':')
  label.textContent = (role === 'ct' ? 'CT 助手' : '您') + ' · ' + ts
  if (role === 'user') label.style.textAlign = 'right'
  bubble.textContent = text
  row.appendChild(label)
  row.appendChild(bubble)
  msgs.appendChild(row)
  msgs.scrollTop = msgs.scrollHeight
}
function sc(){
  const inp = document.getElementById('cin')
  const txt = inp.value.trim()
  if (!txt) return
  inp.value = ''
  addBubble('user', txt)
  window.setTimeout(() => addBubble('ct', '收到。这里是 mock CT 助手视图，后续可以接入真实 agent、审批流和任务查询。'), 450)
}
