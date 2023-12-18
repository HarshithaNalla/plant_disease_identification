const express = require('express');
const app = express();
const port = 3000;
const request = require("request");
const { initializeApp, cert } = require('firebase-admin/app');
const { getFirestore } = require('firebase-admin/firestore');
const serviceAccount = require('./key.json');

initializeApp({
  credential: cert(serviceAccount),
});

const db = getFirestore();

const bodyParser = require('body-parser');
const bcrypt = require('bcrypt');
app.use(bodyParser.urlencoded({ extended: true }));
app.use(express.static('public'));
app.set('view engine', 'ejs');

app.get('/', (req, res) => {
  res.render("login.ejs");
});

app.post('/signinsubmit', async (req, res) => {
  const email_id = req.body.email_id;
  const pass = req.body.pass; // Use req.body to access form data

  try {
    // Query Firestore to find a user with the provided email
    const userRef = db.collection('userDemo').where('email', '==', email_id);
    const snapshot = await userRef.get();

    if (snapshot.empty) {
      // No user found with the provided email
      res.send('Login failed: User not found');
      return;
    }

    // Assuming there's only one user with the provided email
    const userData = snapshot.docs[0].data();
    const hashedPassword = userData.pass;

    // Compare the provided password with the hashed password
    const passwordMatch = await bcrypt.compare(pass, hashedPassword);

    if (passwordMatch) {
      // Passwords match, redirect to another page (e.g., 'main.ejs')
      res.redirect('http://127.0.0.1:8000/');
    } else {
      // Passwords do not match
      res.send('Login failed: Incorrect password');
    }
  } catch (error) {
    console.error('Error:', error);
    res.status(500).send('Error: ' + error.message);
  }
});

app.post('/signupsubmit', async (req, res) => {
  const first_name = req.body.first_name;
  const last_name = req.body.last_name;
  const email_id = req.body.email_id;
  const pass = req.body.pass; // Use req.body to access form data

  try {
    const saltRounds = 10; // Adjust the number of rounds as needed
    const hashedPassword = await bcrypt.hash(pass, saltRounds);

    await db.collection('userDemo').add({
      name: first_name + ' ' + last_name,
      email: email_id,
      pass: hashedPassword,
    });

    // Redirect the user to the signin page after successful signup
    res.redirect('/');
  } catch (error) {
    console.error('Error:', error);
    res.status(500).send('Error: ' + error.message);
  }
});

app.post('/report', async (req, res) => {
  try {
    const fileUrl = req.body.fileUrl; // Assuming the file URL is sent from the client

    // Assuming 'reportedImages' is a Firestore collection for storing reported images
    const reportRef = db.collection('reportedImages').doc();

    await reportRef.set({
      reportedAt: new Date(),
      imageUrl: fileUrl,
    });

    res.json({ message: 'Report submitted successfully' });
  } catch (error) {
    console.error('Error submitting report:', error);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(port, () => {
  console.log(`Example app listening on port ${port}`);
});