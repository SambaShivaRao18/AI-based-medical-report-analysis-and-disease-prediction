// Add this with other requires
const fileUpload = require('express-fileupload');


// server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');

// Load environment variables
dotenv.config();

// Import database connection
const connectDB = require('./config/db');

// Import routes
const authRoutes = require('./routes/auth');

// Initialize express
const app = express();

// Connect to database
connectDB();

// Middleware
app.use(cors({
    origin: 'http://localhost:8000', // Your frontend URL
    credentials: true
}));
app.use(express.json()); // Parse JSON bodies
app.use(express.urlencoded({ extended: true })); // Parse URL-encoded bodies

// Add after other middleware
app.use(fileUpload({
    limits: { fileSize: 20 * 1024 * 1024 }, // 20MB limit
    abortOnLimit: true
}));

// Routes
app.use('/api/auth', authRoutes);

// Add report analysis routes
const reportRoutes = require('./routes/reportAnalysis');
app.use('/api/reports', reportRoutes);

// Test route
app.get('/', (req, res) => {
    res.json({ message: '🚀 Backend server is running!' });
});

// Error handling middleware
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ message: 'Something went wrong!' });
});

// Start server
const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
    console.log(`✅ Server running on http://localhost:${PORT}`);
});