// backend/routes/chatbot.js
const express = require('express');
const router = express.Router();
const axios = require('axios');
const { protect } = require('../middleware/auth');
const ChatHistory = require('../models/ChatHistory'); // We'll create this

// Python Flask server URL
const PYTHON_SERVER_URL = 'http://127.0.0.1:5002';  // Use IPv4 explicitly

// Send message to chatbot
router.post('/message', protect, async (req, res) => {
    try {
        const { message } = req.body;
        
        if (!message) {
            return res.status(400).json({
                success: false,
                error: 'No message provided'
            });
        }

        console.log(`📤 Sending to Python chatbot: ${message.substring(0, 50)}...`);

        // Call Python service
        const response = await axios.post(`${PYTHON_SERVER_URL}/api/chatbot/chat`, {
            message: message,
            userId: req.user.id
        });

        // Save to database (optional)
        try {
            await ChatHistory.create({
                userId: req.user.id,
                userMessage: message,
                botResponse: response.data.response,
                timestamp: new Date()
            });
        } catch (dbError) {
            console.error('Failed to save chat history:', dbError.message);
            // Don't fail the request if saving fails
        }

        res.json({
            success: true,
            response: response.data.response
        });

    } catch (error) {
        console.error('Chatbot error:', error.message);
        res.status(500).json({
            success: false,
            error: error.response?.data?.error || 'Chat service unavailable'
        });
    }
});

// Get chat history
router.get('/history', protect, async (req, res) => {
    try {
        const history = await ChatHistory.find({ userId: req.user.id })
            .sort({ timestamp: -1 })
            .limit(50);
        
        res.json({
            success: true,
            history
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: 'Failed to fetch history'
        });
    }
});

module.exports = router;