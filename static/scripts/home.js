const urlParams = new URLSearchParams(window.location.search);
const tableNo = urlParams.get('table');

if (tableNo === null || tableNo === "") {
    document.getElementById("table-No").innerHTML = "Take a Way";
} else {
    document.getElementById("table-No").innerHTML = "Inside, " + tableNo;
}

