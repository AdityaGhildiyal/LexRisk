const express = require('express');
const router = express.Router();
const reportController = require('../controllers/reportController');

router.get('/report/:id', reportController.showReport);

module.exports = router;
