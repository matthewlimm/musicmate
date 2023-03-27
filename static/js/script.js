function pausePlay(input) {
    console.log(input.tagName);
    var playButton = input.parentElement.querySelector('span');
    pauseButtons = document.getElementsByClassName('fa fa-pause')
    for(i=0;i<pauseButtons.length;i++)
    {
        pauseButtons[i].className = 'fa fa-play';
    }
    if (input.checked || input.tagName == 'FORM')
    {
        playButton.className = "fa fa-pause";
    } 
    else 
    {
        playButton.className = "fa fa-play";
    }
}

function next() {
    window.history.forward();
}

function previous() {
    window.history.back();
}