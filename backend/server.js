// backend/server.js
const express = require('express');
const mongoose = require('mongoose');
const cors = require('cors');
const dotenv = require('dotenv');
const fileUpload = require('express-fileupload');

// Load environment variables
dotenv.config();

// Import database connection
const connectDB = require('./config/db');
const drugRoutes = require('./routes/drugs');

// Import routes
const authRoutes = require('./routes/auth');
const reportRoutes = require('./routes/reportAnalysis');
const chatbotRoutes = require('./routes/chatbot');
const symptomRoutes = require('./routes/symptoms');

// Initialize express
const app = express();

// Connect to database
connectDB();

// CORS configuration - THIS MUST COME BEFORE ROUTES
app.use(cors({
    origin: ['http://localhost:8000', 'http://127.0.0.1:8000'],
    credentials: true,
    methods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
    allowedHeaders: ['Content-Type', 'Authorization', 'Origin', 'X-Requested-With', 'Accept']
}));

// Handle preflight requests
app.options('*', cors());

// Middleware
app.use(express.json());
app.use(express.urlencoded({ extended: true }));
app.use(fileUpload({
    limits: { fileSize: 20 * 1024 * 1024 },
    abortOnLimit: true
}));

// Routes
app.use('/api/drugs', drugRoutes);
app.use('/api/auth', authRoutes);
app.use('/api/reports', reportRoutes);
app.use('/api/chatbot', chatbotRoutes);
app.use('/api/symptoms', symptomRoutes);

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