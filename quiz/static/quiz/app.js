(function(){
  const $ = (id)=> document.getElementById(id);
  const pad = (n)=> String(n).padStart(2,'0');
  const msToClock = (ms)=> { const s=Math.floor(ms/1000); const mm=Math.floor(s/60), ss=s%60; return `${pad(mm)}:${pad(ss)}` };

  // ---------- Host page ----------
  async function hostInit(){
    if(!$('createRoomBtn')) return;
    const joinBase = window.location.origin + '/join/?room=';

    $('createRoomBtn').onclick = async ()=>{
      const code = ($('roomCodeHost').value || '').trim().toUpperCase();
      if(!code){ alert('Enter room code'); return; }
      const res = await fetch('/api/room/create/', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({code})});
      const data = await res.json();
      $('roomLive').innerText = data.code;
      $('joinLink').innerText = joinBase + data.code;
      startWS(data.code);
      refreshLeaderboard(data.code);
    };

    $('closeRoomBtn').onclick = async ()=>{
      const code = ($('roomLive').innerText || '').trim();
      if(!code){ alert('No room yet'); return; }
      await fetch(`/api/room/${code}/close/`, {method:'POST'});
      alert('Room closed');
    };

    async function refreshLeaderboard(code){
      const res = await fetch(`/api/room/${code}/leaderboard/`);
      const data = await res.json();
      renderLeaderboard(data.leaderboard || []);
    }

    function renderLeaderboard(list){
      list.sort((a,b)=> (b.score - a.score) || (a.timeMs - b.timeMs));
      const rows = list.map((s,i)=>`
        <tr>
          <td>${i===0?'🥇':i===1?'🥈':i===2?'🥉':i+1}</td>
          <td>${s.name}</td>
          <td>${s.roll}</td>
          <td>${s.className}</td>
          <td><b>${s.score}</b></td>
          <td>${msToClock(s.timeMs || 0)}</td>
        </tr>`).join('');
      $('leaderboardTable').innerHTML = `
        <table><thead><tr><th>#</th><th>Name</th><th>Roll</th><th>Class</th><th>Score</th><th>Time</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="6" class="note">No submissions yet.</td></tr>'}</tbody></table>`;
    }

    let socket = null;
    function startWS(code){
      if(socket) { socket.close(); socket = null; }
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      socket = new WebSocket(`${proto}://${location.host}/ws/leaderboard/${code}/`);
      socket.onmessage = (ev)=>{
        try{ const data = JSON.parse(ev.data); renderLeaderboard(data); } catch(e){}
      };
      socket.onclose = ()=>{};
    }

    // Auto-start if /host/?room=CODE
    const params = new URLSearchParams(location.search);
    const pre = (params.get('room')||'').toUpperCase();
    if(pre){
      $('roomCodeHost').value = pre;
      $('createRoomBtn').click();
    }
  }

  // ---------- Player page ----------
  async function playerInit(){
    if(!$('joinBtn')) return;

    let startTime = null, timerInt = null, roomCode = null, playerRoll = null;

    function startTimer(){
      startTime = Date.now();
      timerInt = setInterval(()=>{
        $('liveTimer').innerText = msToClock(Date.now() - startTime);
      }, 200);
    }
    function stopTimer(){ if(timerInt){ clearInterval(timerInt); timerInt=null; } }

    $('joinBtn').onclick = async ()=>{
      const code = ($('roomCode').value||'').trim().toUpperCase();
      const name = ($('name').value||'').trim();
      const roll = ($('roll').value||'').trim();
      const className = ($('className').value||'').trim();
      const inst = ($('inst').value||'').trim();
      if(!code || !name || !roll || !className){ alert('Fill Room, Name, Roll, Class'); return; }

      const jr = await fetch(`/api/room/${code}/join/`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({name, roll, class_name: className, inst})});
      if(!jr.ok){ alert('Failed to join (room closed or invalid)'); return; }
      roomCode = code; playerRoll = roll;

      const qr = await fetch(`/api/room/${code}/quiz/`);
      const qd = await qr.json();
      renderQuestions(qd.quiz || []);

      $('quizCard').style.display = '';
      $('resultCard').style.display = 'none';
      startTimer();
      window.scrollTo(0,0);
    };

    function renderQuestions(QUIZ){
      const wrap = $('questions'); wrap.innerHTML = '';
      QUIZ.forEach((item, idx)=>{
        const div = document.createElement('div'); div.className = 'q';
        div.innerHTML = `<h3>${idx+1}. ${item.q}</h3>`;
        const opts = document.createElement('div'); opts.className = 'options';
        item.opts.forEach((opt, i)=>{
          const label = document.createElement('label'); label.className='opt';
          label.innerHTML = `<input type="radio" name="q${idx}" value="${i}"> <span>${String.fromCharCode(65+i)}) ${opt}</span>`;
          opts.appendChild(label);
        });
        div.appendChild(opts); wrap.appendChild(div);
      });
      $('submitBtn').onclick = async ()=>{
        const answers = QUIZ.map((_, idx)=>{
          const c = document.querySelector(`input[name="q${idx}"]:checked`);
          return c ? Number(c.value) : -1;
        });
        if(answers.includes(-1)){
          if(!confirm('Some questions are unanswered. Submit anyway?')) return;
        }
        stopTimer();
        const time_ms = Date.now() - startTime;
        const res = await fetch(`/api/room/${roomCode}/submit/`, {
          method:'POST', headers:{'Content-Type':'application/json'},
          body: JSON.stringify({roll: playerRoll, answers, time_ms})
        });
        if(!res.ok){ alert('Submit failed'); return; }
        const data = await res.json();
        $('studentName').innerText = ($('name').value||'').trim();
        $('scoreVal').innerText = data.score;
        $('timeVal').innerText = msToClock(time_ms);
        renderExplain(data.detail || []);
        $('resultCard').style.display = '';
        window.scrollTo(0,0);
      };
    }

    function renderExplain(detail){
      const box = $('explanations'); box.innerHTML = '';
      detail.forEach(d=>{
        const p = document.createElement('p');
        p.innerHTML = `<b>Q${d.idx+1}:</b> <span class="${d.correct?'good':'bad'}">${d.correct?'✓ Correct':'✗ Not expected answer'}</span><br><span class="note">${d.explain}</span>`;
        box.appendChild(p);
      });
    }

    // prefill room from URL
    const params = new URLSearchParams(location.search);
    const pre = (params.get('room')||'').toUpperCase();
    if(pre) $('roomCode').value = pre;
  }

  hostInit();
  playerInit();
})();
