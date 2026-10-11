ADMIN_HTML = r'''<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>WePulse 管理中心</title>
  <style>
    :root{color-scheme:light;--ink:#17211b;--muted:#67716b;--brand:#16784a;--line:#dfe7e1;--soft:#f3f7f4;--bad:#b42318}
    *{box-sizing:border-box}body{margin:0;background:#eef3ef;color:var(--ink);font:15px/1.55 system-ui,"Microsoft YaHei",sans-serif}
    main{max-width:1100px;margin:auto;padding:28px 18px 60px}header{display:flex;gap:18px;align-items:center;justify-content:space-between;flex-wrap:wrap}
    h1{margin:0;font-size:30px}h2{margin:0 0 14px;font-size:19px}.sub{color:var(--muted)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:18px}
    section{background:white;border:1px solid var(--line);border-radius:14px;padding:18px;box-shadow:0 4px 18px #1934250b}.wide{grid-column:1/-1}
    input,button{font:inherit;border-radius:9px;border:1px solid var(--line);padding:10px 12px}input{width:100%;background:white}button{cursor:pointer;background:var(--brand);border-color:var(--brand);color:white;font-weight:650}button.alt{background:white;color:var(--ink)}button.danger{background:white;color:var(--bad);border-color:#f0b9b5}
    .row{display:flex;gap:9px;align-items:center}.row input{flex:1}.toolbar{display:flex;gap:8px;flex-wrap:wrap}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(135px,1fr));gap:10px}.metric{background:var(--soft);padding:12px;border-radius:10px}.metric b{display:block;font-size:20px}.ok{color:var(--brand)}.bad{color:var(--bad)}
    table{width:100%;border-collapse:collapse}th,td{text-align:left;border-bottom:1px solid var(--line);padding:10px 7px;vertical-align:top}th{font-size:13px;color:var(--muted)}a{color:var(--brand)}code{font-size:12px}.notice{display:none;margin-top:16px;padding:12px 14px;border-radius:10px;background:#fff4e5;border:1px solid #ffd59a}.error{color:var(--bad);max-width:420px;word-break:break-word}.empty{color:var(--muted);padding:12px 0}@media(max-width:720px){table{display:block;overflow:auto}.row{align-items:stretch;flex-direction:column}}
  </style>
</head>
<body><main>
  <header><div><h1>WePulse</h1><div class="sub">微信公众号更新监测管理中心</div></div><div class="toolbar"><a href="/docs" target="_blank">接口文档</a><a href="/feeds/all.xml" target="_blank">聚合 RSS</a><a href="/api/digest" target="_blank">今日摘要</a></div></header>
  <div id="notice" class="notice"></div>
  <div class="grid">
    <section class="wide"><h2>首次使用前确认</h2><ol><li><b>首次安装保持联网：</b>Windows 需要可用的 WinGet，启动脚本会自动准备 uv 和 Python 3.12。</li><li><b>本机接入微信读书 Cookie：</b>浏览器登录微信读书后，从 <code>weread.qq.com</code> 请求的 Request Headers 中复制完整 Cookie，并在下方安全录入。不要把 Cookie 发给任何人、聊天工具或公开仓库。</li></ol><p class="sub">Cookie 保存后会立即生效，无需编辑配置文件或重启。建议首次只添加一个公众号完成验证。</p></section>
    <section><h2>登录</h2><div class="row"><input id="token" type="password" placeholder="ADMIN_TOKEN"><button onclick="login()">保存并刷新</button></div><p class="sub">令牌只保存在当前浏览器的 localStorage，不会显示在页面或返回结果中。</p></section>
    <section><h2>运行状态</h2><div id="status" class="cards"><div class="empty">请先填写管理令牌</div></div></section>
    <section class="wide"><h2>录入或更新微信读书 Cookie</h2><div class="row"><input id="wereadCookie" type="password" autocomplete="off" spellcheck="false" placeholder="粘贴完整 Cookie（至少包含 wr_vid 和 wr_skey）"><button onclick="saveCookie()">安全保存</button></div><p class="sub">Cookie 只写入本机 <code>.env</code>，不会回显、不会存入浏览器 localStorage。保存后输入框会立即清空。</p></section>
    <section class="wide"><h2>快捷操作</h2><div class="toolbar"><button onclick="collectAll()">立即采集全部</button><button class="alt" onclick="checkCookie()">检查 Cookie</button><button class="alt" onclick="testNotify()">测试每日推送</button><button class="alt" onclick="reloadAll()">刷新页面</button></div><p class="sub">Cookie 检查会使用第一个微信读书订阅执行一次真实采集；没有订阅时只能确认是否已配置。</p></section>
    <section class="wide"><h2>通过微信原文添加公众号</h2><div class="row"><input id="articleUrl" placeholder="https://mp.weixin.qq.com/s/..."><button onclick="addArticle()">识别并添加</button></div></section>
    <section class="wide"><h2>订阅与失败提示</h2><div id="accounts" class="empty">尚未加载</div></section>
    <section class="wide"><h2>最近 48 小时文章</h2><div id="articles" class="empty">尚未加载</div></section>
  </div>
</main><script>
const $=id=>document.getElementById(id), esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
$('token').value=localStorage.getItem('wepulseToken')||'';
function notice(message,bad=false){const n=$('notice');n.style.display='block';n.className='notice'+(bad?' error':'');n.textContent=message;setTimeout(()=>n.style.display='none',7000)}
async function api(path,options={}){const token=$('token').value.trim();const headers={...(options.headers||{}),'Authorization':'Bearer '+token};if(options.body)headers['Content-Type']='application/json';const r=await fetch(path,{...options,headers});let data;try{data=await r.json()}catch{data=await r.text()}if(!r.ok)throw new Error(data.detail||data||('HTTP '+r.status));return data}
function login(){localStorage.setItem('wepulseToken',$('token').value.trim());reloadAll()}
async function reloadAll(){try{const [s,a,items]=await Promise.all([api('/api/status'),api('/api/accounts'),api('/api/articles?hours=48')]);renderStatus(s);renderAccounts(a);renderArticles(items)}catch(e){notice(e.message,true)}}
function renderStatus(s){$('status').innerHTML=`<div class="metric"><span>订阅</span><b>${s.accounts.total}</b></div><div class="metric"><span>失败</span><b class="${s.accounts.failed?'bad':'ok'}">${s.accounts.failed}</b></div><div class="metric"><span>Cookie</span><b class="${s.weread.status==='ok'?'ok':s.weread.status==='error'?'bad':''}">${esc(s.weread.label)}</b></div><div class="metric"><span>每日任务</span><b>${String(s.schedule.hour).padStart(2,'0')}:${String(s.schedule.minute).padStart(2,'0')}</b></div>`}
function renderAccounts(rows){if(!rows.length){$('accounts').innerHTML='<div class="empty">还没有订阅，请在上方粘贴一篇微信原文链接。</div>';return}$('accounts').innerHTML='<table><thead><tr><th>公众号</th><th>采集器</th><th>最后检查</th><th>状态</th><th>操作</th></tr></thead><tbody>'+rows.map(a=>`<tr><td><b>${esc(a.name)}</b></td><td>${esc(a.connector)}</td><td>${esc(a.last_checked_at||'尚未检查')}</td><td class="${a.last_error?'error':'ok'}">${esc(a.last_error||'正常')}</td><td><div class="toolbar"><button class="alt" onclick="collectOne(${a.id})">采集</button><button class="danger" onclick="removeAccount(${a.id})">删除</button></div></td></tr>`).join('')+'</tbody></table>'}
function renderArticles(rows){if(!rows.length){$('articles').innerHTML='<div class="empty">最近 48 小时没有记录。</div>';return}$('articles').innerHTML='<table><thead><tr><th>公众号</th><th>标题</th><th>发布时间</th></tr></thead><tbody>'+rows.map(a=>`<tr><td>${esc(a.account_name)}</td><td><a href="${esc(a.url)}" target="_blank" rel="noopener">${esc(a.title)}</a></td><td>${esc(a.published_at)}</td></tr>`).join('')+'</tbody></table>'}
async function addArticle(){try{const r=await api('/api/accounts/from-article',{method:'POST',body:JSON.stringify({url:$('articleUrl').value.trim()})});notice('已添加：'+r.account_name);$('articleUrl').value='';await reloadAll()}catch(e){notice(e.message,true)}}
async function collectAll(){try{notice('正在采集，请稍候……');const r=await api('/api/collect',{method:'POST'});notice(`采集完成：${r.reduce((n,x)=>n+(x.inserted||0),0)} 篇新增`);await reloadAll()}catch(e){notice(e.message,true)}}
async function collectOne(id){try{const r=await api(`/api/accounts/${id}/collect`,{method:'POST'});notice(r.error?r.error:`采集完成：${r.inserted||0} 篇新增`,!!r.error);await reloadAll()}catch(e){notice(e.message,true)}}
async function checkCookie(){try{const r=await api('/api/checks/weread',{method:'POST'});notice(r.message,r.status==='error');await reloadAll()}catch(e){notice(e.message,true)}}
async function saveCookie(){const input=$('wereadCookie'),cookie=input.value.trim();if(!cookie){notice('请先粘贴完整 Cookie',true);return}try{const r=await api('/api/config/weread-cookie',{method:'PUT',body:JSON.stringify({cookie})});input.value='';notice(r.message);await reloadAll()}catch(e){notice(e.message,true)}}
async function testNotify(){try{const r=await api('/api/notifications/test',{method:'POST'});const pairs=Object.entries(r.results).map(([k,v])=>k+': '+v).join('；');notice(pairs||'未配置任何推送渠道',!r.ok)}catch(e){notice(e.message,true)}}
async function removeAccount(id){if(!confirm('确定删除这个订阅及其历史文章吗？此操作不可撤销。'))return;try{await api(`/api/accounts/${id}`,{method:'DELETE'});notice('订阅已删除');await reloadAll()}catch(e){notice(e.message,true)}}
if($('token').value)reloadAll();
</script></body></html>'''
