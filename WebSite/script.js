// DRAGON DATA API CONSTANTS - CHANGE VERSION WHEN NEEDED
const DDRAGON_VERSION = "14.3.1";
const CHAMP_DATA_URL = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/data/pt_BR/champion.json`;
const CHAMP_IMG_URL = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/`;
const API_URL = "http://127.0.0.1:8000/predict";

// CBLol Teams CHANGE THIS LATER IF NEEDED
const cblolTeams = [
    "LOUD", "paiN Gaming", "FURIA", "RED Canids", 
    "Vivo Keyd Stars", "Fluxo", "Leviatán", "Isurus"
];

let allChampions = [];

async function loadChampions() {
    try {
        const response = await fetch(CHAMP_DATA_URL);
        const data = await response.json();
        allChampions = Object.values(data.data);
        renderGrid(allChampions);
    } catch (error) {
        console.error("Erro:", error);
    }
}

function populateTeamSelects() {
    const blueSelect = document.getElementById('blue-team-select');
    const redSelect = document.getElementById('red-team-select');

    cblolTeams.forEach(team => {
        blueSelect.add(new Option(team, team));
        redSelect.add(new Option(team, team));
    });
}

function renderGrid(champs) {
    const grid = document.getElementById('champion-grid');
    grid.innerHTML = '';
    
    champs.forEach(champ => {
        const item = document.createElement('div');
        item.className = 'champ-item';
        item.id = champ.id; 
        item.draggable = true;
        item.ondragstart = drag;
        
        item.innerHTML = `
            <img src="${CHAMP_IMG_URL}${champ.image.full}" alt="${champ.name}">
            <div class="name-overlay text-white">${champ.name}</div>
        `;
        grid.appendChild(item);
    });
}

document.getElementById('champ-search').addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allChampions.filter(c => c.name.toLowerCase().includes(term));
    renderGrid(filtered);
});

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.closest('.champ-item').id);
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drop(ev) {
    ev.preventDefault();
    const champId = ev.dataTransfer.getData("text");
    const targetSlot = ev.target.closest('.slot');
    
    if (targetSlot) {
        targetSlot.classList.remove('filled');
        targetSlot.innerHTML = `
            <img src="${CHAMP_IMG_URL}${champId}.png" class="slot-img" style="width:100%; height:100%; object-fit:cover; position:absolute; top:0; left:0; opacity:0.6;">
            <span class="slot-label" style="position:relative; z-index:2; font-weight:bold; text-shadow: 2px 2px 4px black;">${champId}</span>
        `;
        targetSlot.classList.add('filled');
        targetSlot.setAttribute('data-champion', champId);
    }
}

// helper to generate streak icon in HTML
function getStreakHtml(streak) {
    if (streak > 0) {
        return `<span class="fw-bold" style="color: #ff6b6b;"><i class="fa-solid fa-fire"></i> ${streak}</span>`;
    } else {
        return `<span class="fw-bold" style="color: #4dabf7;"><i class="fa-regular fa-snowflake"></i> ${Math.abs(streak)}</span>`;
    }
}

document.getElementById('predict-btn').addEventListener('click', async () => {
    
    const blueTeam = document.getElementById('blue-team-select').value;
    const redTeam = document.getElementById('red-team-select').value;
    
    if(!blueTeam || !redTeam) {
        alert("Por favor, selecione os dois times.");
        return;
    }

    const getChamps = (sideId) => {
        const slots = document.getElementById(sideId).querySelectorAll('.slot');
        return Array.from(slots).map(slot => slot.getAttribute('data-champion'));
    };

    const blueChamps = getChamps('blue-slots');
    const redChamps = getChamps('red-slots');

    if (blueChamps.includes(null) || redChamps.includes(null)) {
        alert("Por favor, preencha todos os 10 campeões.");
        return;
    }

    try {
        const response = await fetch(API_URL, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                blue_team: blueTeam,
                red_team: redTeam,
                blue_champs: blueChamps,
                red_champs: redChamps
            })
        });

        if (!response.ok) throw new Error("Erro na API");

        const result = await response.json();
        
        document.getElementById('analysis-section').style.display = 'block';
        
        // fill blue/red win percentages
        document.getElementById('blue-win-percent').innerText = `${result.blue_win_percent}%`;
        document.getElementById('red-win-percent').innerText = `${result.red_win_percent}%`;
        
        // fillm ain status table
        const tbody = document.getElementById('stats-table-body');
        tbody.innerHTML = '';

        for(let i=0; i<5; i++) {
            const blue = result.blue_stats[i];
            const red = result.red_stats[i];
            
            const row = `
                <tr>
                    <td class="fw-bold gold-text">${blue.role}</td>
                    <td class="text-info fw-bold">${blue.player}</td>
                    <td><span class="badge bg-secondary">${blue.mastery}</span></td>
                    <td>${getStreakHtml(blue.streak)}</td>
                    <td class="text-muted">vs</td>
                    <td class="text-danger fw-bold">${red.player}</td>
                    <td><span class="badge bg-secondary">${red.mastery}</span></td>
                    <td>${getStreakHtml(red.streak)}</td>
                </tr>
            `;
            tbody.innerHTML += row;
        }

        // fill comparison table
        const comparisonBody = document.getElementById('comparison-table-body');
        comparisonBody.innerHTML = '';

        result.comparison.forEach(row => {
            // determine colors based on edge
            const mColor = row.mastery_edge === 'Blue' ? 'text-info' : 'text-danger';
            const fColor = row.form_edge === 'Blue' ? 'text-info' : 'text-danger';
            
            // translate
            const mEdgeText = row.mastery_edge === 'Blue' ? 'Azul' : 'Vermelho';
            const fEdgeText = row.form_edge === 'Blue' ? 'Azul' : 'Vermelho';

            const tr = `
                <tr>
                    <td class="fw-bold text-white">${row.role}</td>
                    <td class="${mColor} fw-bold">+${row.mastery_val}% ${mEdgeText}</td>
                    <td class="${fColor} fw-bold">+${row.form_val}% ${fEdgeText}</td>
                </tr>
            `;
            comparisonBody.innerHTML += tr;
        });

        document.getElementById('analysis-section').scrollIntoView({ behavior: 'smooth' });

    } catch (error) {
        console.error(error);
        alert("Erro ao conectar com o servidor de análise.");
    }
});

loadChampions();
populateTeamSelects();