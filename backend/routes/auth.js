const { protect } = require('../middleware/auth');
// routes/auth.js
const express = require('express');
const router = express.Router();
const jwt = require('jsonwebtoken');
const User = require('../models/User');

// Generate JWT Token
const generateToken = (id) => {
    return jwt.sign({ id }, process.env.JWT_SECRET, {
        expiresIn: process.env.JWT_EXPIRE
    });
};

// @route   POST /api/auth/register
// @desc    Register a new user
// @access  Public
router.post('/register', async (req, res) => {
    try {
        const { name, email, phoneNumber, password, role, ...otherData } = req.body;

        // Check if user already exists
        const userExists = await User.findOne({ 
            $or: [{ email }, { phoneNumber }] 
        });

        if (userExists) {
            return res.status(400).json({ 
                message: 'User already exists with this email or phone number' 
            });
        }

        // Create new user
        const user = await User.create({
            name,
            email,
            phoneNumber,
            password,
            role,
            ...otherData
        });

        // Generate token
        const token = generateToken(user._id);

        res.status(201).json({
            success: true,
            token,
            user: {
                id: user._id,
                name: user.name,
                email: user.email,
                phoneNumber: user.phoneNumber,
                role: user.role
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ 
            message: 'Server error', 
            error: error.message 
        });
    }
});

// @route   POST /api/auth/login
// @desc    Login user
// @access  Public
router.post('/login', async (req, res) => {
    try {
        const { email, password } = req.body;

        // Check if email and password are provided
        if (!email || !password) {
            return res.status(400).json({ 
                message: 'Please provide email and password' 
            });
        }

        // Find user by email and include password field
        const user = await User.findOne({ email }).select('+password');

        if (!user) {
            return res.status(401).json({ 
                message: 'Invalid credentials' 
            });
        }

        // Check password
        const isPasswordMatch = await user.comparePassword(password);

        if (!isPasswordMatch) {
            return res.status(401).json({ 
                message: 'Invalid credentials' 
            });
        }

        // Generate token
        const token = generateToken(user._id);

        res.status(200).json({
            success: true,
            token,
            user: {
                id: user._id,
                name: user.name,
                email: user.email,
                phoneNumber: user.phoneNumber,
                role: user.role
            }
        });
    } catch (error) {
        console.error(error);
        res.status(500).json({ 
            message: 'Server error', 
            error: error.message 
        });
    }
});

// @route   GET /api/auth/me
// @desc    Get current logged in user
// @access  Private
router.get('/me', async (req, res) => {
    try {
        // Get token from header
        const token = req.header('Authorization')?.replace('Bearer ', '');
        
        if (!token) {
            return res.status(401).json({ message: 'No token, authorization denied' });
        }

        // Verify token
        const decoded = jwt.verify(token, process.env.JWT_SECRET);
        
        // Find user
        const user = await User.findById(decoded.id).select('-password');
        
        if (!user) {
            return res.status(401).json({ message: 'User not found' });
        }

        res.json({
            success: true,
            user
        });
    } catch (error) {
        res.status(401).json({ message: 'Token is not valid' });
    }
});

router.get('/me', protect, async (req, res) => {
    res.json({
        success: true,
        user: req.user
    });
});
module.exports = router;