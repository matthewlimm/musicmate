function pausePlay(input) {
    console.log(input);
    pauseButtons = document.getElementsByClassName('fa fa-pause')
    for(i=0;i<pauseButtons.length;i++)
    {
        pauseButtons[i].className = 'fa fa-play';
    }
    if(typeof input === 'string' || input instanceof String)
    {
      var playButton = document.getElementById(input).querySelector('span');
      playButton.className = "fa fa-pause";
      return;
    }
    var playButton = input.parentElement.querySelector('span');
    if(input.checked)
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

function preview(URL) {
    'use strict';
    
    const context = new AudioContext();
    const playButton = document.querySelector('#play');
      
    let yodelBuffer;
  
    window.fetch(URL)
      .then(response => response.arrayBuffer())
      .then(arrayBuffer => context.decodeAudioData(arrayBuffer))
      .then(audioBuffer => {
        playButton.disabled = false;
        yodelBuffer = audioBuffer;
      });
      
      playButton.onclick = () => play(yodelBuffer);
  
    function play(audioBuffer) {
      const source = context.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(context.destination);
      source.start();
    }
  }

  function toggleDropdown(event) {
    // Stop the click from propagating to the window (which would close the dropdown)
    event.stopPropagation();

    // Toggle the display of the dropdown content
    const dropdownContent = event.currentTarget.querySelector('.dropdown-content');
    dropdownContent.style.display = dropdownContent.style.display === 'block' ? 'none' : 'block';
}

// Close the dropdown if the user clicks outside of it
window.onclick = function(event) {
    if (!event.target.closest('.user-button')) {
        const dropdowns = document.querySelectorAll('.dropdown-content');
        dropdowns.forEach(dropdown => {
            dropdown.style.display = 'none';
        });
    }
}