import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { Container, Nav, Navbar } from 'react-bootstrap';
import MatchPredictions from './components/MatchPredictions';
import Dashboard from './pages/Dashboard';
import TeamDetail from './pages/TeamDetail';
import 'bootstrap/dist/css/bootstrap.min.css';
import './App.css';

function App() {
  return (
    <Router>
      <div className="app-wrapper">
        <Navbar bg="primary" variant="dark" expand="lg">
          <Container>
            <Navbar.Brand as={Link} to="/">
              IPL Player Prediction 2025
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="ms-auto">
                <Nav.Link as={Link} to="/" className="nav-item-custom">Dashboard</Nav.Link>
                <Nav.Link as={Link} to="/predictions" className="nav-item-custom">Match Predictions</Nav.Link>
              </Nav>
            </Navbar.Collapse>
          </Container>
        </Navbar>

        <Container fluid className="main-content py-4">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/predictions" element={<MatchPredictions />} />
            <Route path="/team/:teamSlug" element={<TeamDetail />} />
          </Routes>
        </Container>
      </div>
    </Router>
  );
}

export default App; 