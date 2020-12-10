const displayBlockOnWindowLoad = () => {
    // Get element
    const javascriptAccordion = document.getElementById('javascript-accordion')

    javascriptAccordion.style.display = 'block';
}

window.onload = displayBlockOnWindowLoad();