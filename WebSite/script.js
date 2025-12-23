const DDRAGON_VERSION = "14.3.1"; // current patch ver. UPDATE IF NEEDED
const CHAMP_DATA_URL = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/data/pt_BR/champion.json`;
const CHAMP_IMG_URL = `https://ddragon.leagueoflegends.com/cdn/${DDRAGON_VERSION}/img/champion/`;

// get champion data from ddragon
async function loadChampions() {
    try {
        const response = await fetch(CHAMP_DATA_URL);
        const data = await response.json();
        const champions = Object.values(data.data);
        renderCarousel(champions);
    } catch (error) {
        console.error("Erro ao carregar campeões:", error);
    }
}

// render carousel
function renderCarousel(champs) {
    const container = document.getElementById('carousel-content');
    container.innerHTML = ''; // clear previous content
    
    const itemsPerSlide = 6; 
    for (let i = 0; i < champs.length; i += itemsPerSlide) {
        const chunk = champs.slice(i, i + itemsPerSlide);
        const isActive = i === 0 ? 'active' : '';
        
        const slide = document.createElement('div');
        slide.className = `carousel-item ${isActive}`;
        
        const flexContainer = document.createElement('div');
        flexContainer.className = 'd-flex justify-content-center gap-3';
        
        chunk.forEach(champ => {
            const card = `
                <div class="champ-card" draggable="true" ondragstart="drag(event)" id="${champ.id}">
                    <img src="${CHAMP_IMG_URL}${champ.image.full}" class="champ-icon" alt="${champ.name}">
                    <div class="champ-name-label">${champ.name}</div>
                </div>
            `;
            flexContainer.innerHTML += card;
        });
        
        slide.appendChild(flexContainer);
        container.appendChild(slide);
    }
}


function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.closest('.champ-card').id);
}

function allowDrop(ev) {
    ev.preventDefault();
}

function drop(ev) {
    ev.preventDefault();
    const champId = ev.dataTransfer.getData("text");
    const targetSlot = ev.target.closest('.slot');
    

    targetSlot.innerHTML = `
        <img src="${CHAMP_IMG_URL}${champId}.png" class="slot-img">
        <span class="slot-label">${champId}</span>
    `;
    targetSlot.classList.add('filled');
    targetSlot.setAttribute('data-champion', champId);
}


loadChampions();