// backend/routes/reportAnalysis.js
const express = require('express');
const router = express.Router();
const axios = require('axios');
const FormData = require('form-data');
const { protect } = require('../middleware/auth');
const Report = require('../models/Report'); // We'll create this model

// Python Flask server URL
const PYTHON_SERVER_URL = 'http://127.0.0.1:5001';  // Use IPv4 explicitly

// Analyze report endpoint
router.post('/analyze', protect, async (req, res) => {
    try {
        // Forward the request to Python server
        const formData = new FormData();
        
        // Add form fields
        formData.append('patient_name', req.body.patient_name);
        formData.append('age', req.body.age);
        formData.append('gender', req.body.gender);
        formData.append('userId', req.user.id);
        
        // Add file if exists
        if (req.files && req.files.pdf_file) {
            formData.append('pdf_file', req.files.pdf_file.data, {
                filename: req.files.pdf_file.name,
                contentType: req.files.pdf_file.mimetype
            });
        }

        // Make request to Python service
        const response = await axios.post(
            `${PYTHON_SERVER_URL}/api/report-analyzer/analyze`,
            formData,
            {
                headers: {
                    ...formData.getHeaders(),
                },
                maxContentLength: Infinity,
                maxBodyLength: Infinity
            }
        );

        // Save report to MongoDB
        const report = new Report({
            userId: req.user.id,
            patientName: req.body.patient_name,
            age: req.body.age,
            gender: req.body.gender,
            analysis: response.data.analysis,
            modelUsed: response.data.model_used,
            createdAt: new Date()
        });

        await report.save();

        res.json({
            success: true,
            analysis: response.data.analysis,
            reportId: report._id
        });

    } catch (error) {
        console.error('Error calling Python service:', error.message);
        res.status(500).json({
            success: false,
            error: error.response?.data?.error || 'Analysis failed'
        });
    }
});

// Get user's reports
router.get('/reports', protect, async (req, res) => {
    try {
        const reports = await Report.find({ userId: req.user.id })
            .sort({ createdAt: -1 })
            .limit(10);
        
        res.json({
            success: true,
            reports
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: 'Failed to fetch reports'
        });
    }
});

// Get single report
router.get('/reports/:id', protect, async (req, res) => {
    try {
        const report = await Report.findOne({
            _id: req.params.id,
            userId: req.user.id
        });
        
        if (!report) {
            return res.status(404).json({
                success: false,
                error: 'Report not found'
            });
        }
        
        res.json({
            success: true,
            report
        });
    } catch (error) {
        res.status(500).json({
            success: false,
            error: 'Failed to fetch report'
        });
    }
});

module.exports = router;