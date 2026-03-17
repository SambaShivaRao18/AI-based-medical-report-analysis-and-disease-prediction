// backend/routes/drugs.js
const express = require('express');
const router = express.Router();
const axios = require('axios');
const { protect } = require('../middleware/auth');

const PYTHON_SERVER_URL = 'http://127.0.0.1:5004';

// Check drug interactions
router.post('/interactions', protect, async (req, res) => {
    try {
        const { medications } = req.body;
        
        console.log('📥 Node.js received medications:', medications);
        
        if (!medications || medications.length < 2) {
            return res.status(400).json({
                success: false,
                error: 'Please provide at least 2 medications'
            });
        }

        console.log(`📤 Forwarding to Python: ${PYTHON_SERVER_URL}/api/drugs/interactions`);

        const response = await axios.post(`${PYTHON_SERVER_URL}/api/drugs/interactions`, {
            medications: medications
        }, {
            timeout: 30000,
            headers: { 'Content-Type': 'application/json' }
        });

        console.log('✅ Python response received');

        return res.json({
            success: true,
            interactions: response.data.interactions,
            statistics: response.data.statistics,
            used_fallback: response.data.used_fallback,
            unknown_drugs: response.data.unknown_drugs
        });

    } catch (error) {
        console.error('❌ Node.js error:', error.message);
        
        if (error.code === 'ECONNREFUSED') {
            return res.status(503).json({
                success: false,
                error: 'Drug interaction service not running. Please start Python server on port 5004.'
            });
        }
        
        return res.status(500).json({
            success: false,
            error: error.response?.data?.error || error.message
        });
    }
});

// Test endpoint without auth
router.post('/test', async (req, res) => {
    try {
        const { medications } = req.body;
        console.log('📥 Test endpoint:', medications);
        
        const response = await axios.post(`${PYTHON_SERVER_URL}/api/drugs/interactions`, {
            medications: medications
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
        const response = await axios.get(`${PYTHON_SERVER_URL}/api/drugs/health`);
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