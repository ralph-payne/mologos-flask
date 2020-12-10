/* Disable Search Button if text input is empty */
const checkTextFieldIsNotEmpty = () => {
    const navSearchBarInput = document.getElementById('nav-search-bar-input-element')
    const magnifyingGlassSearch = document.getElementById('navbar-magnifying-glass-search')

    if (navSearchBarInput.value.length > 0) { 
        magnifyingGlassSearch.disabled = false;
    } else { 
        magnifyingGlassSearch.disabled = true;
    }
}