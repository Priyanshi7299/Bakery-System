import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

function App() {
  const [products, setProducts] = useState([]);
  const [cart, setCart] = useState([]);
  const [customerName, setCustomerName] = useState('');
  const [customerEmail, setCustomerEmail] = useState('');
  const [orderStatus, setOrderStatus] = useState(null);
  const [orderId, setOrderId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchProducts();
  }, []);

  const fetchProducts = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/products`);
      // Convert prices from $ to Rs. (multiplying by 75 for conversion)
      const productsWithRupees = response.data.map(product => ({
        ...product,
        displayPrice: product.price * 75, // Convert to Rupees for display
        price: product.price // Keep original price for backend
      }));
      setProducts(productsWithRupees);
      setError(null);
    } catch (err) {
      setError('Failed to fetch products. Please try again later.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const addToCart = (product) => {
    const existingItem = cart.find(item => item.id === product.id);
    
    if (existingItem) {
      setCart(cart.map(item => 
        item.id === product.id 
          ? { ...item, quantity: item.quantity + 1 } 
          : item
      ));
    } else {
      setCart([...cart, { ...product, quantity: 1 }]);
    }
  };

  const removeFromCart = (productId) => {
    setCart(cart.filter(item => item.id !== productId));
  };

  const updateQuantity = (productId, newQuantity) => {
    if (newQuantity < 1) return;
    
    setCart(cart.map(item => 
      item.id === productId 
        ? { ...item, quantity: newQuantity } 
        : item
    ));
  };

  const calculateTotal = () => {
    return cart.reduce((total, item) => total + (item.price * item.quantity), 0).toFixed(2);
  };

  const calculateDisplayTotal = () => {
    return cart.reduce((total, item) => total + (item.displayPrice * item.quantity), 0).toFixed(2);
  };

  const placeOrder = async () => {
    if (!customerName || !customerEmail || cart.length === 0) {
      setError('Please fill in your details and add items to cart');
      return;
    }

    try {
      const response = await axios.post(`${API_URL}/orders`, {
        customer_name: customerName,
        customer_email: customerEmail,
        items: cart.map(item => ({
          product_id: item.id,
          quantity: item.quantity
        }))
      });

      setOrderId(response.data.order_id);
      setOrderStatus('Order placed successfully! We are processing your order.');
      setCart([]);
      setCustomerName('');
      setCustomerEmail('');
      setError(null);
    } catch (err) {
      setError('Failed to place order. Please try again.');
      console.error(err);
    }
  };

  const checkOrderStatus = async () => {
    if (!orderId) {
      setError('Please enter an order ID');
      return;
    }

    try {
      const response = await axios.get(`${API_URL}/orders/${orderId}`);
      setOrderStatus(`Order #${orderId} status: ${response.data.status}`);
      setError(null);
    } catch (err) {
      setError('Failed to check order status. Please verify your order ID.');
      console.error(err);
    }
  };

  return (
    <div className="App">
      <header className="bakery-header">
        <div className="header-content">
          <h1>Welcome to Priyanshi's Bakery</h1>
          <p className="tagline">Delicious treats baked with love ♥</p>
        </div>
      </header>

      <div className="container">
        <div className="products-section">
          <h2>Our Delightful Creations</h2>
          {loading && <div className="loading">Loading delicious treats...</div>}
          {error && <p className="error">{error}</p>}
          
          <div className="products-grid">
            {products.map(product => (
              <div key={product.id} className="product-card">
                <div className="product-image">
                  {/* Decorative element to represent product */}
                  <div className="product-image-placeholder"></div>
                </div>
                <div className="product-details">
                  <h3>{product.name}</h3>
                  <p className="product-description">{product.description}</p>
                  <p className="price">₹{product.displayPrice.toFixed(2)}</p>
                  <button 
                    className="add-to-cart-btn"
                    onClick={() => addToCart(product)}
                    disabled={!product.in_stock}
                  >
                    {product.in_stock ? 'Add to Cart' : 'Out of Stock'}
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>

        <div className="cart-order-container">
          <div className="order-section">
            <h2>Your Sweet Selection</h2>
            
            {cart.length === 0 ? (
              <p className="empty-cart">Your cart is empty. Add some delicious treats!</p>
            ) : (
              <>
                <div className="cart-items">
                  {cart.map(item => (
                    <div key={item.id} className="cart-item">
                      <div className="cart-item-details">
                        <h4>{item.name}</h4>
                        <p>₹{item.displayPrice.toFixed(2)} each</p>
                      </div>
                      <div className="cart-item-actions">
                        <div className="quantity-controls">
                          <button onClick={() => updateQuantity(item.id, item.quantity - 1)}>-</button>
                          <span>{item.quantity}</span>
                          <button onClick={() => updateQuantity(item.id, item.quantity + 1)}>+</button>
                        </div>
                        <p className="item-total">₹{(item.displayPrice * item.quantity).toFixed(2)}</p>
                        <button className="remove-btn" onClick={() => removeFromCart(item.id)}>×</button>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="cart-total">
                  <span>Total:</span>
                  <span>₹{calculateDisplayTotal()}</span>
                </div>

                <div className="customer-form">
                  <h3>Your Details</h3>
                  <div className="form-group">
                    <label htmlFor="name">Name:</label>
                    <input 
                      type="text" 
                      id="name" 
                      value={customerName} 
                      onChange={(e) => setCustomerName(e.target.value)} 
                      placeholder="Enter your name"
                      required 
                    />
                  </div>
                  <div className="form-group">
                    <label htmlFor="email">Email:</label>
                    <input 
                      type="email" 
                      id="email" 
                      value={customerEmail} 
                      onChange={(e) => setCustomerEmail(e.target.value)} 
                      placeholder="Enter your email"
                      required 
                    />
                  </div>
                  <button onClick={placeOrder} className="order-button">Place Order</button>
                </div>
              </>
            )}
          </div>

          <div className="order-status-section">
            <h2>Track Your Order</h2>
            <div className="order-status-form">
              <input 
                type="number" 
                placeholder="Enter Order ID" 
                value={orderId || ''} 
                onChange={(e) => setOrderId(e.target.value)} 
              />
              <button onClick={checkOrderStatus}>Check Status</button>
            </div>
            {orderStatus && <p className="status-message">{orderStatus}</p>}
          </div>
        </div>
      </div>
      
      <footer className="bakery-footer">
        <p>Priyanshi's Bakery © 2025 | Made with ♥ and flour</p>
      </footer>
    </div>
  );
}

export default App;