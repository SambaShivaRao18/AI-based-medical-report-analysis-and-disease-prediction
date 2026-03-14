// backend/routes/symptoms.js
const express = require('express');
const router = express.Router();
const axios = require('axios');
const { protect } = require('../middleware/auth');

// Add CORS headers for all responses in this route
router.use((req, res, next) => {
    res.header('Access-Control-Allow-Origin', 'http://localhost:8000');
    res.header('Access-Control-Allow-Headers', 'Origin, X-Requested-With, Content-Type, Accept, Authorization');
    res.header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    res.header('Access-Control-Allow-Credentials', 'true');
    
    // Handle preflight requests
    if (req.method === 'OPTIONS') {
        return res.status(200).end();
    }
    next();
});

const PYTHON_SERVER_URL = 'http://127.0.0.1:5003';

// Predict disease from symptoms
router.post('/predict', protect, async (req, res) => {
    try {
        const { symptoms } = req.body;
        
        console.log('📥 Node.js received symptoms:', symptoms);
        
        if (!symptoms || symptoms.length < 2) {
            return res.status(400).json({
                success: false,
                error: 'Please select at least 2 symptoms'
            });
        }

        console.log(`📤 Forwarding to Python: ${PYTHON_SERVER_URL}/api/symptoms/predict`);
        
        // Forward to Python service
        const response = await axios.post(`${PYTHON_SERVER_URL}/api/symptoms/predict`, {
            symptoms: symptoms
        });

        console.log('✅ Python response received');

        // Return exactly what Python sent
        return res.json({
            success: true,
            predictions: response.data.predictions,
            used_fallback: response.data.used_fallback,
            unknown_symptoms: response.data.unknown_symptoms
        });

    } catch (error) {
        console.error('❌ Node.js error:', error.message);
        
        if (error.code === 'ECONNREFUSED') {
            return res.status(503).json({
                success: false,
                error: 'Symptom checker service not running. Please start Python server on port 5003.'
            });
        }
        
        return res.status(500).json({
            success: false,
            error: error.message
        });
    }
});

// Test endpoint without auth (for debugging)
router.post('/test', async (req, res) => {
    try {
        const { symptoms } = req.body;
        console.log('📥 Test endpoint:', symptoms);
        
        const response = await axios.post(`${PYTHON_SERVER_URL}/api/symptoms/predict`, {
            symptoms: symptoms
        });
        
        res.json(response.data);
    } catch (error) {
        console.error('Test error:', error.message);
        res.status(500).json({ error: error.message });
    }
});

// Health check
router.get('/health', async (req, res) => {
    try {
        const response = await axios.get(`${PYTHON_SERVER_URL}/api/symptoms/health`);
        res.json({ 
            success: true, 
            python: response.data,
            node: 'connected'
        });
    } catch (error) {
        res.json({ 
            success: false, 
            error: 'Python service not reachable',
            node: 'running but python disconnected'
        });
    }
});

module.exports = router;