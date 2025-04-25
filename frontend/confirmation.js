const orderId = new URLSearchParams(window.location.search).get("order_id");
console.log("orderId =", orderId);

function reloadOrderInfo() {
    fetch(`http://localhost:5000/order/${orderId}`)
        .then(res => res.json())
        .then(data => {
            console.log("Données de commande reçues :", data);
            const order = data.order;
            document.getElementById("order-info").innerHTML = `
                <strong>ID :</strong> ${order.id}<br>
                <strong>Total (avant taxes) :</strong> $${order.total_price.toFixed(2)}<br>
                <strong>Payé :</strong> ${order.paid ? "Oui" : "Non"}<br>
                <strong>Nombre de produits :</strong> ${order.products.length}
            `;
            renderProductDetails(order.products);
        });
}

function toggleProductDetails() {
  const content = document.getElementById("product-details");
  const icon = document.getElementById("dropdown-icon");

  // Remove the inline display:none style first
  content.removeAttribute("style");

  if (content.classList.contains("open")) {
    content.classList.remove("open");
    icon.className = "fas fa-chevron-down";
  } else {
    content.classList.add("open");
    icon.className = "fas fa-chevron-up";
  }
}

function renderProductDetails(products) {
    const container = document.getElementById("product-details");
    container.innerHTML = "";

    products.forEach(p => {
        const line = document.createElement("div");
        line.className = "product-line";

        const total = (p.price * p.quantity).toFixed(2);
        const imageId = p.id - 1;

        line.innerHTML = `
            <img src="/img/${imageId}.jpg" alt="${p.name}" />
            <div class="product-info-small">
                <p><strong>${p.name}</strong></p>
                <p>Prix unitaire : $${p.price.toFixed(2)}</p>
                <p>Quantité : ${p.quantity}</p>
                <p>Sous-total : $${total}</p>
            </div>
        `;
        container.appendChild(line);
    });
}

function setupPaymentHandler() {
    document.getElementById("confirm-payment").onclick = () => {
        const card = {
            name: document.getElementById("card-name").value,
            number: document.getElementById("card-number").value,
            expiration_month: document.getElementById("card-exp-month").value.trim(),
            expiration_year: document.getElementById("card-exp-year").value.trim(),
            cvv: document.getElementById("card-cvv").value.trim()
        };

        if (!Object.values(card).every(v => v)) {
            alert("Veuillez remplir tous les champs de la carte.");
            return;
        }

        fetch(`http://localhost:5000/order/${orderId}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({credit_card: card})
        })
            .then(res => res.json())
            .then(data => {
                const jobId = data.job_id;
                if (!jobId) {
                    alert("Erreur : ID du job introuvable.");
                    return;
                }

                document.getElementById("payment-form").innerHTML = `<p>Paiement en cours... (Job ID: ${jobId})</p>`;

                const interval = setInterval(() => {
                    fetch(`http://localhost:5000/job/${jobId}`)
                        .then(res => res.json())
                        .then(job => {
                            if (job.status === "finished") {
                                clearInterval(interval);
                                fetch(`http://localhost:5000/order/${orderId}`)
                                    .then(res => res.json())
                                    .then(orderRes => {
                                        if (orderRes.order.paid) {
                                            document.getElementById("payment-form").innerHTML = `
                                            <p style="color: green;"><strong>Paiement effectué avec succès !</strong></p>`;
                                        } else {
                                            renderPaymentForm("Le paiement a échoué. Vérifiez les informations de carte.");
                                        }
                                        reloadOrderInfo();
                                    });
                            } else if (job.status === "failed") {
                                clearInterval(interval);
                                renderPaymentForm("Échec du paiement. Veuillez réessayer.");
                            }
                        });
                }, 2000);
            })
            .catch(err => alert("Erreur lors du paiement : " + err));
    };
}

function setupNavToggle() {
    const buttons = document.querySelectorAll(".nav-btn");

    buttons.forEach(btn => {
        btn.addEventListener("click", () => {
            // Remove "active" class from all buttons
            buttons.forEach(b => b.classList.remove("active"));
            // Add to the clicked one
            btn.classList.add("active");

            const targetId = btn.dataset.target;

            // Hide all sections
            document.getElementById("order-info").style.display = "none";
            document.getElementById("shipping-form").style.display = "none";
            document.getElementById("payment-form").style.display = "none";

            // Show the target section
            const target = document.getElementById(targetId);
            if (target) {
                target.style.display = "block";
            }
        });
    });
}


function renderPaymentForm(errorMsg = "") {
    document.getElementById("payment-form").innerHTML = `
        <h3>Informations de carte bancaire</h3>
        ${errorMsg ? `<p style="color:red;"><strong>${errorMsg}</strong></p>` : ""}
        <input type="text" id="card-name" placeholder="Nom sur la carte" required/>
        <input type="text" id="card-number" placeholder="Numéro de carte" required/>
        <input type="text" id="card-exp-month" placeholder="Mois d'expiration (MM)" required/>
        <input type="text" id="card-exp-year" placeholder="Année d'expiration (YYYY)" required/>
        <input type="text" id="card-cvv" placeholder="CVV" required/>
        <button id="confirm-payment">Valider le paiement</button>
    `;
    setupPaymentHandler();
}

document.addEventListener("DOMContentLoaded", () => {
    reloadOrderInfo();
    setupNavToggle()
    document.getElementById("next-shipping").onclick = () => {
        document.getElementById("shipping-form").style.display = "block";
        document.getElementById("next-shipping").style.display = "none";
    };

    document.getElementById("submit-shipping").onclick = () => {
        const email = document.getElementById("email").value.trim();
        const shipping_information = {
            country: document.getElementById("country").value.trim(),
            address: document.getElementById("address").value.trim(),
            postal_code: document.getElementById("postal_code").value.trim(),
            city: document.getElementById("city").value.trim(),
            province: document.getElementById("province").value
        };

        if (!email || Object.values(shipping_information).some(val => val === "")) {
            alert("Veuillez remplir tous les champs d’adresse avant de confirmer.");
            return;
        }

        fetch(`http://localhost:5000/order/${orderId}`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({order: {email, shipping_information}})
        })
            .then(res => res.json())
            .then(() => {
                alert("Informations de livraison enregistrées !");
                document.getElementById("shipping-form").style.display = "none";
                document.getElementById("payment-form").style.display = "block";
                renderPaymentForm();  // render payment fields fresh
            })
            .catch(err => alert("Erreur d'enregistrement : " + err));
    };

    setupPaymentHandler();
});
