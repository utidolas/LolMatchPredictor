const DDRAGON_VERSION = "14.3.1";
const CHAMP_DATA_URL = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/data/pt_BR/champion.json`;
const CHAMP_IMG_URL = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/`;

// Official 2025 LTA South Teams
const cblolTeams = [
    "LOUD",
    "paiN Gaming",
    "FURIA",
    "RED Canids",
    "Vivo Keyd Stars",
    "Fluxo",
    "Leviatán",
    "Isurus"
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

function populateTeamSelects() {
    const blueSelect = document.getElementById('blue-team-select');
    const redSelect = document.getElementById('red-team-select');

    cblolTeams.forEach(team => {
        // Create option for Blue
        const optBlue = document.createElement('option');
        optBlue.value = team;
        optBlue.textContent = team;
        blueSelect.appendChild(optBlue);

        // Create option for Red
        const optRed = document.createElement('option');
        optRed.value = team;
        optRed.textContent = team;
        redSelect.appendChild(optRed);
    });
}

// Filtro de Busca
document.getElementById('champ-search').addEventListener('input', (e) => {
    const term = e.target.value.toLowerCase();
    const filtered = allChampions.filter(c => c.name.toLowerCase().includes(term));
    renderGrid(filtered);
});


function drag(ev) {
    // Garante que estamos pegando o ID do elemento .champ-item
    const champId = ev.target.closest('.champ-item').id;
    ev.dataTransfer.setData("text", champId);
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drop(ev) {
    ev.preventDefault();
    const champId = ev.dataTransfer.getData("text");
    const targetSlot = ev.target.closest('.slot');
    
    if (targetSlot) {
        // Remove a classe 'filled' se já houver para resetar visual
        targetSlot.classList.remove('filled');
        
        // Insere a imagem e o nome
        targetSlot.innerHTML = `
            <img src="${CHAMP_IMG_URL}${champId}.png" class="slot-img" style="width:100%; height:100%; object-fit:cover; position:absolute; top:0; left:0; opacity:0.6;">
            <span class="slot-label" style="position:relative; z-index:2; font-weight:bold; text-shadow: 2px 2px 4px black;">${champId}</span>
        `;
        
        targetSlot.classList.add('filled');
        targetSlot.setAttribute('data-champion', champId);
    }
}

// Init
loadChampions();
populateTeamSelects();