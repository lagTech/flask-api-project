let currentPage = 1;
const limit = 12;
const cart = {};

function fetchProducts(page = 1) {
    fetch(`http://localhost:5000/?page=${page}&limit=${limit}`)
        .then(response => response.json())
        .then(data => {
            displayProducts(data.products);
            setupPagination(data.total, data.page);
        })
        .catch(error => {
            console.error("Erreur lors de la récupération des produits:", error);
        });
}

// function displayProducts(products) {
//   const container = document.getElementById("products-container");
//   container.innerHTML = "";
//   products.forEach(product => {
//     const card = document.createElement("div");
//     card.className = "card";
//
//     const img = document.createElement("img");
//     img.src = "https://via.placeholder.com/150";
//     img.alt = product.name;
//
//     const name = document.createElement("h3");
//     name.textContent = product.name;
//
//     const description = document.createElement("p");
//     description.textContent = product.description || "Pas de description.";
//
//     const price = document.createElement("p");
//     price.innerHTML = `<strong>Prix:</strong> $${product.price.toFixed(2)}`;
//
//     const weight = document.createElement("p");
//     weight.innerHTML = `<strong>Poids:</strong> ${product.weight} g`;
//
//     const btn = document.createElement("button");
//     btn.textContent = "Ajouter au panier";
//     btn.onclick = () => addToCart(product);
//
//     card.appendChild(img);
//     card.appendChild(name);
//     card.appendChild(description);
//     card.appendChild(price);
//     card.appendChild(weight);
//     card.appendChild(btn);
//
//     container.appendChild(card);
//   });
// }

function displayProducts(products) {
    const container = document.getElementById("products-container");
    container.innerHTML = "";

    products.forEach(product => {
        const card = document.createElement("div");
        card.className = "card";

        const img = document.createElement("img");
        const imageId = product.id - 1;  // car 0.jpeg correspond à l'ID 1
        img.src = `/img/${imageId}.jpg`;
        img.alt = product.name;
        if (!product.in_stock) {

        }

        const name = document.createElement("h3");
        name.textContent = product.name;

        const description = document.createElement("p");
        description.textContent = product.description || "Pas de description.";

        const price = document.createElement("p");
        price.innerHTML = `<strong>Prix:</strong> $${product.price.toFixed(2)}`;

        const weight = document.createElement("p");
        weight.innerHTML = `<strong>Poids:</strong> ${product.weight} g`;

        const btn = document.createElement("button");
        btn.textContent = product.in_stock ? "Ajouter au panier" : "Rupture de stock";
        btn.disabled = !product.in_stock;
        btn.style.backgroundColor = product.in_stock ? "#007BFF" : "#ccc";
        btn.style.cursor = product.in_stock ? "pointer" : "not-allowed";

        if (product.in_stock) {
            btn.onclick = () => addToCart(product);
        }

        const contentWrapper = document.createElement("div");
        contentWrapper.style.flexGrow = "1";
        contentWrapper.appendChild(img);
        contentWrapper.appendChild(name);
        contentWrapper.appendChild(description);
        contentWrapper.appendChild(price);
        contentWrapper.appendChild(weight);

        card.appendChild(contentWrapper);

        // if (!product.in_stock) {
        //     const badge = document.createElement("span");
        //     badge.textContent = "Rupture de stock";
        //     badge.style.color = "#fff";
        //     badge.style.background = "#d11a2a";
        //     badge.style.padding = "3px 6px";
        //     badge.style.borderRadius = "5px";
        //     badge.style.fontSize = "12px";
        //     badge.style.marginTop = "5px";
        //     card.appendChild(badge);
        // }

        card.appendChild(btn);
        container.appendChild(card);
    });
}

function addToCart(product) {
    if (cart[product.id]) {
        cart[product.id].quantity += 1;
    } else {
        cart[product.id] = {...product, quantity: 1};
    }
    renderCart();
}

function removeFromCart(productId) {
    delete cart[productId];
    renderCart();
}


function updateQuantity(productId, quantity) {
    const qty = parseInt(quantity);
    if (qty <= 0) {
        removeFromCart(productId);
    } else {
        cart[productId].quantity = qty;
        renderCart();
    }
}

function renderCart() {
    const cartItems = document.getElementById("cart-items");
    cartItems.innerHTML = "";

    Object.values(cart).forEach(item => {
        const totalPerItem = (item.price * item.quantity).toFixed(2);

        const div = document.createElement("div");
        div.className = "cart-item";

        div.innerHTML = `
      <img src="/frontend/static/img/${item.id - 1}.jpg" alt="${item.name}">
      <div class="cart-item-info">
        <p><strong>${item.name}</strong></p>
        <p>Prix unitaire : $${item.price.toFixed(2)}</p>
        <p><strong>Total : $${totalPerItem}</strong></p>
        <input type="number" min="1" value="${item.quantity}" onchange="updateQuantity(${item.id}, this.value)">
      </div>
      <button class="trash-btn" onclick="removeFromCart(${item.id})">
        <i class="fas fa-trash-alt"></i>
      </button>
    `;

        cartItems.appendChild(div);
    });
}


function setupPagination(total, page) {
    const pages = Math.ceil(total / limit);
    const paginationContainer = document.getElementById("pagination");
    paginationContainer.innerHTML = "";

    for (let i = 1; i <= pages; i++) {
        const btn = document.createElement("button");
        btn.textContent = i;
        btn.onclick = () => {
            currentPage = i;
            fetchProducts(i);
        };
        if (i === page) btn.disabled = true;
        paginationContainer.appendChild(btn);
    }
}

function submitOrder() {
    const products = Object.values(cart).map(item => ({
        id: item.id,
        quantity: item.quantity
    }));

    if (products.length === 0) {
        alert("Votre panier est vide !");
        return;
    }

    fetch("http://localhost:5000/order", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({products})  // <-- CORRECTED HERE
    })
        .then(response => {
            if (!response.ok) {
                throw new Error("Erreur lors de la commande");
            }
            return response.json();
        })
        .then(data => {
            alert(`Commande envoyée avec succès ! ID de commande : ${data.order_id}`);
            window.location.href = `http://localhost:5000/frontend/confirmation.html?order_id=${data.order_id}`;
        })
        .catch(error => {
            alert("Une erreur lors de l'envoi de la commande.");
            console.error(error);
        });
}

document.addEventListener("DOMContentLoaded", () => {
    fetchProducts(currentPage);
});

// Fonction pour basculer l'état du menu hamburger
  function toggleMenu() {
    const menuItems = document.getElementById('menuItems');
    const menuOverlay = document.getElementById('menuOverlay');

    menuItems.classList.toggle('active');
    menuOverlay.classList.toggle('active');
  }