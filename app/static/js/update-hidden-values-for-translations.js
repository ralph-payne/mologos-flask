/* Script to Update Hidden Values for Translations */
const fetchInput = (element) => {
    event.preventDefault(element)

    // Fetch values
    srcVal = document.getElementById("text-to-translate").value;
    srcLng = document.getElementById("select-language").value;

    if (element.id == "translate-btn") {
        // Assign values to hidden input
        document.getElementById("src-tra-1").value = srcVal;
        document.getElementById("dst-lng-1").value = srcLng;

        document.getElementById("form-translate-api").submit();
    } else {
        dstVal = document.getElementById("translation-result").value;

        document.getElementById("src-tra-2").value = srcVal;
        document.getElementById("dst-lng-2").value = srcLng;
        document.getElementById("dst-tra-2").value = dstVal;

        document.getElementById("form-add-translation-to-db").submit();
    }
}