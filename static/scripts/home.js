const urlParams = new URLSearchParams(window.location.search);
const tableNo = urlParams.get('table');

if (tableNo === null || tableNo === "") {
    document.getElementById("table-No").innerHTML = "Take a Way";
} else {
    document.getElementById("table-No").innerHTML = "Inside, " + tableNo;
}

let currentPage = 1;
document.getElementById('loadMore').addEventListener('click', function() {
    currentPage++;
    fetch(`/regular-menu?page=${currentPage}`)
        .then(response => response.json())
        .then(data => {
            if(data.items.length < 20) {
                this.style.display = 'none';
            }
        });
});
