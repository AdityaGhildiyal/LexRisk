const express = require('express');
const path = require('path');
const session = require('express-session');
const helmet = require('helmet');
const morgan = require('morgan');
const uploadRoutes = require('./routes/upload');
const reportRoutes = require('./routes/report');

const app = express();
const PORT = process.env.PORT || 3000;

// Security
app.use(helmet({ contentSecurityPolicy: false }));
app.use(morgan('combined'));

// View engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// Static files
app.use(express.static(path.join(__dirname, 'public')));

// Session (stores report data in memory for demo)
app.use(session({
  secret: process.env.SESSION_SECRET || 'lexrisk-demo-secret',
  resave: false,
  saveUninitialized: false,
  cookie: { maxAge: 60 * 60 * 1000 } // 1 hour
}));

app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/', uploadRoutes);
app.use('/', reportRoutes);

// 404
app.use((req, res) => {
  res.status(404).render('upload', { error: 'Page not found' });
});

// Error handler
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).render('upload', { error: 'An unexpected error occurred. Please try again.' });
});

app.listen(PORT, () => {
  console.log(`LexRisk web service running at http://localhost:${PORT}`);
});

module.exports = app;
