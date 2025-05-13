//Name: Arthur Milner ID: 21035478
//E-Mail: arthur2.milner@live.uwe.ac.uk

//Code for the hamburger menu
const hamburger = document.getElementById('hamburger');
const navUL = document.getElementById('nav-bar-ul');

hamburger.addEventListener('click', () => {
    navUL.classList.toggle('open');
});

//Code for the modal
const openModalButtons = document.querySelectorAll('[data-modal-target]')
const closeModalButtons = document.querySelectorAll('[data-close-button]')
const overlay = document.getElementById('overlay')

openModalButtons.forEach(button => {
    button.addEventListener('click', () => {
        const modal = document.querySelector(button.dataset.modalTarget)
        openModal(modal)
    })
})

overlay.addEventListener('click', () => {
    const modals = document.querySelectorAll('.modal.active')
    modals.forEach(modal => {
        closeModal(modal)
    })
})

closeModalButtons.forEach(button => {
    button.addEventListener('click', () => {
        const modal = button.closest('.modal')
        closeModal(modal)
    })
})

function openModal(modal) {
    if (modal == null) return
    modal.classList.add('active')
    overlay.classList.add('active')
}

function closeModal(modal) {
    if (modal == null) return
    modal.classList.remove('active')
    overlay.classList.remove('active')
}

//Setting to toggle dark mode
function darkMode() {
    document.body.classList.toggle("dark-mode");
}

//Function to validate text fields which should take only number inputs
function checkNumber(id, event){
    var character = String.fromCharCode(event.which);
    if(!(/[0-9]/.test(character))){ /* Checks if input is number */
        event.preventDefault(); /* Prevents input being added */
        document.getElementById(id).style.borderColor = "red";
    }
    else{
        document.getElementById(id).style.borderColor = "white";
    }
}

//Functions to validate dates
function setenddate(){
    var selectedstartdate = document.getElementById("startdate").value;
    document.getElementById("enddate").min = selectedstartdate;
}
function initialdate(){
    var today=new Date();
    var year = today.getFullYear();
    var month = today.getMonth() + 1;
    var day = today.getDate();
    if (month < 10) {
        month = '0' + month; 
    }
    if (day < 10) {
        day = '0' + day; 
    }
    today = year + '-' + month + '-' + day;           
    document.getElementById("startdate").min = today;
    document.getElementById("enddate").min = today;        
}





