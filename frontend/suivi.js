const jobId = new URLSearchParams(window.location.search).get("job_id");

function checkStatus() {
  if (!jobId) {
    document.getElementById("status").textContent = "Aucun ID de job fourni.";
    return;
  }

  fetch(`http://localhost:5000/job/${jobId}`)
    .then((res) => res.json())
    .then((data) => {
      const status = data.status;
      const result = data.result;
      const display = document.getElementById("status");

      if (status === "finished") {
        display.innerHTML = `<strong>Paiement terminé avec succès !</strong><br/>Transaction : ${JSON.stringify(result)}`;
      } else if (status === "failed") {
        display.innerHTML = `<strong>Le paiement a échoué.</strong>`;
      } else {
        display.textContent = `Statut actuel : ${status}`;
      }
    })
    .catch((err) => {
      document.getElementById("status").textContent = "Erreur lors de la récupération du statut.";
      console.error(err);
    });
}

document.getElementById("refresh-btn").onclick = checkStatus;

document.addEventListener("DOMContentLoaded", checkStatus);
