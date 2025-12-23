// ===== drag and drop script for champion selection ===== 
function allowDrop(ev) {
    ev.preventDefault();
}

function drag(ev) {
    ev.dataTransfer.setData("text", ev.target.id);
}

function drop(ev) {
    ev.preventDefault();
    var data = ev.dataTransfer.getData("text");
    var champName = data;
    
    // Altera o conteúdo do slot para o nome do campeão
    var targetSlot = ev.target.closest('.slot');
    targetSlot.innerHTML = `<strong>${champName}</strong>`;
    targetSlot.classList.add('filled');
    
    console.log("Campeão " + champName + " colocado na rota " + targetSlot.dataset.role);
}