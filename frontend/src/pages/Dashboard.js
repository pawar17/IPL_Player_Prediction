import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { getMatches } from '../api';

const Dashboard = () => {
    const [matches, setMatches] = useState([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        loadMatches();
    }, []);

    const loadMatches = async () => {
        try {
            const data = await getMatches();
            setMatches(data.slice(0, 6)); // Get first 6 upcoming matches
            setLoading(false);
        } catch (err) {
            console.error('Failed to load matches:', err);
            setLoading(false);
        }
    };

    const teams = [
        { name: 'Chennai Super Kings', slug: 'csk', className: 'team-csk' },
        { name: 'Mumbai Indians', slug: 'mi', className: 'team-mi' },
        { name: 'Royal Challengers Bangalore', slug: 'rcb', className: 'team-rcb' },
        { name: 'Kolkata Knight Riders', slug: 'kkr', className: 'team-kkr' },
        { name: 'Delhi Capitals', slug: 'dc', className: 'team-dc' },
        { name: 'Punjab Kings', slug: 'pbks', className: 'team-pbks' },
        { name: 'Rajasthan Royals', slug: 'rr', className: 'team-rr' },
        { name: 'Sunrisers Hyderabad', slug: 'srh', className: 'team-srh' }
    ];

    const handleTeamClick = (teamSlug) => {
        navigate(`/team/${teamSlug}`);
    };

    return (
        <Container>
            {/* Hero Section */}
            <div className="hero-section mb-5">
                <h1 className="display-5 mb-3">
                    IPL 2025 Player Predictions
                </h1>
                <p className="lead mb-4">
                    Performance predictions for all 72 matches of IPL 2025
                </p>
                <Button
                    variant="primary"
                    size="lg"
                    onClick={() => navigate('/predictions')}
                >
                    View Predictions
                </Button>
            </div>

            {/* Stats Cards */}
            <Row className="mb-5">
                <Col md={3} sm={6} className="mb-3">
                    <Card className="stat-card h-100">
                        <Card.Body>
                            <div className="stat-number">72</div>
                            <p className="stat-label mb-0">Matches</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3} sm={6} className="mb-3">
                    <Card className="stat-card h-100">
                        <Card.Body>
                            <div className="stat-number">8</div>
                            <p className="stat-label mb-0">Teams</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3} sm={6} className="mb-3">
                    <Card className="stat-card h-100">
                        <Card.Body>
                            <div className="stat-number">120+</div>
                            <p className="stat-label mb-0">Players</p>
                        </Card.Body>
                    </Card>
                </Col>
                <Col md={3} sm={6} className="mb-3">
                    <Card className="stat-card h-100">
                        <Card.Body>
                            <div className="stat-number">Mar-May</div>
                            <p className="stat-label mb-0">Season</p>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {/* Upcoming Matches */}
            <div className="mb-5">
                <h2 className="section-title mb-4">Upcoming Matches</h2>
                {loading ? (
                    <div className="text-center py-5">
                        <div className="spinner-border text-primary" role="status">
                            <span className="visually-hidden">Loading...</span>
                        </div>
                    </div>
                ) : (
                    <Row>
                        {matches.map((match) => (
                            <Col md={6} lg={4} key={match.match_no} className="mb-4">
                                <Card className="match-card h-100">
                                    <Card.Body>
                                        <div className="match-badge mb-3">
                                            Match {match.match_no}
                                        </div>
                                        <h5 className="match-teams mb-3">
                                            {match.team1}
                                            <span className="vs-text mx-2">vs</span>
                                            {match.team2}
                                        </h5>
                                        <div className="match-details">
                                            <div className="mb-2">
                                                <strong>Date:</strong> {match.date}
                                            </div>
                                            <div className="mb-2">
                                                <strong>Time:</strong> {match.time}
                                            </div>
                                            <div className="mb-3">
                                                <strong>Venue:</strong> {match.venue}
                                            </div>
                                        </div>
                                        <Button
                                            variant="outline-primary"
                                            size="sm"
                                            className="w-100"
                                            onClick={() => navigate('/predictions')}
                                        >
                                            View Predictions
                                        </Button>
                                    </Card.Body>
                                </Card>
                            </Col>
                        ))}
                    </Row>
                )}
            </div>

            {/* Teams Section */}
            <div className="mb-5">
                <h2 className="section-title mb-4">Teams</h2>
                <Row>
                    {teams.map((team, index) => (
                        <Col md={3} sm={6} key={index} className="mb-3">
                            <Card
                                className={`team-card ${team.className}`}
                                onClick={() => handleTeamClick(team.slug)}
                            >
                                <Card.Body>
                                    <h6 className="team-name mb-0">{team.name}</h6>
                                </Card.Body>
                            </Card>
                        </Col>
                    ))}
                </Row>
            </div>
        </Container>
    );
};

export default Dashboard;
