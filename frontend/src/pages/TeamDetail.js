import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Container, Row, Col, Card, Button, Table, Spinner, Alert } from 'react-bootstrap';
import axios from 'axios';

const TeamDetail = () => {
    const { teamSlug } = useParams();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [teamData, setTeamData] = useState(null);
    const [error, setError] = useState(null);

    const teamInfo = {
        'csk': { name: 'Chennai Super Kings', className: 'team-csk', shortName: 'CSK' },
        'mi': { name: 'Mumbai Indians', className: 'team-mi', shortName: 'MI' },
        'rcb': { name: 'Royal Challengers Bangalore', className: 'team-rcb', shortName: 'RCB' },
        'kkr': { name: 'Kolkata Knight Riders', className: 'team-kkr', shortName: 'KKR' },
        'dc': { name: 'Delhi Capitals', className: 'team-dc', shortName: 'DC' },
        'pbks': { name: 'Punjab Kings', className: 'team-pbks', shortName: 'PBKS' },
        'rr': { name: 'Rajasthan Royals', className: 'team-rr', shortName: 'RR' },
        'srh': { name: 'Sunrisers Hyderabad', className: 'team-srh', shortName: 'SRH' }
    };

    const currentTeam = teamInfo[teamSlug];

    useEffect(() => {
        if (currentTeam) {
            fetchTeamData();
        }
    }, [teamSlug]);

    const fetchTeamData = async () => {
        setLoading(true);
        setError(null);

        try {
            const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:5000';

            // Fetch team roster and predictions
            const [rosterResponse, predictionsResponse] = await Promise.all([
                axios.get(`${API_BASE_URL}/api/team/${currentTeam.shortName}/roster`),
                axios.get(`${API_BASE_URL}/api/team/${currentTeam.shortName}/predictions`)
            ]);

            setTeamData({
                roster: rosterResponse.data,
                predictions: predictionsResponse.data
            });
        } catch (err) {
            console.error('Error fetching team data:', err);
            setError('Unable to fetch team data. Please try again later.');
        } finally {
            setLoading(false);
        }
    };

    if (!currentTeam) {
        return (
            <Container className="py-5">
                <Alert variant="danger">
                    Team not found. Please select a valid team.
                </Alert>
                <Button variant="primary" onClick={() => navigate('/')}>
                    Back to Dashboard
                </Button>
            </Container>
        );
    }

    if (loading) {
        return (
            <Container className="py-5 text-center">
                <Spinner animation="border" variant="primary" />
                <p className="mt-3">Loading team data...</p>
            </Container>
        );
    }

    return (
        <Container className="py-4">
            {/* Team Header */}
            <div className="mb-4">
                <Button
                    variant="outline-primary"
                    onClick={() => navigate('/')}
                    className="mb-3"
                >
                    &larr; Back to Dashboard
                </Button>

                <Card className={`${currentTeam.className} team-card mb-4`}>
                    <Card.Body className="py-4">
                        <h1 className="team-name display-5 mb-0">{currentTeam.name}</h1>
                    </Card.Body>
                </Card>
            </div>

            {/* Season Predictions */}
            <div className="mb-4">
                <h2 className="section-title mb-4">Season Predictions 2025</h2>
                <Row>
                    <Col md={3} sm={6} className="mb-3">
                        <Card className="stat-card h-100">
                            <Card.Body>
                                <div className="stat-number">{teamData?.predictions?.wins || 0}</div>
                                <p className="stat-label mb-0">Predicted Wins</p>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={3} sm={6} className="mb-3">
                        <Card className="stat-card h-100">
                            <Card.Body>
                                <div className="stat-number">{teamData?.predictions?.losses || 0}</div>
                                <p className="stat-label mb-0">Predicted Losses</p>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={3} sm={6} className="mb-3">
                        <Card className="stat-card h-100">
                            <Card.Body>
                                <div className="stat-number">#{teamData?.predictions?.position || 'N/A'}</div>
                                <p className="stat-label mb-0">Predicted Position</p>
                            </Card.Body>
                        </Card>
                    </Col>
                    <Col md={3} sm={6} className="mb-3">
                        <Card className="stat-card h-100">
                            <Card.Body>
                                <div className="stat-number">{teamData?.predictions?.winPercentage || 0}%</div>
                                <p className="stat-label mb-0">Win Percentage</p>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>

                <Row className="mt-3">
                    <Col md={6} className="mb-3">
                        <Card>
                            <Card.Body>
                                <h5 className="mb-3">Top Performers</h5>
                                <div className="mb-2">
                                    <strong>Top Scorer:</strong> {teamData?.predictions?.topScorer || 'N/A'}
                                </div>
                                <div className="mb-2">
                                    <strong>Top Wicket Taker:</strong> {teamData?.predictions?.topWicketTaker || 'N/A'}
                                </div>
                                <div>
                                    <strong>Average Team Score:</strong> {teamData?.predictions?.averageScore || 'N/A'}
                                </div>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            </div>

            {/* Team Roster */}
            <div className="mb-4">
                <h2 className="section-title mb-4">Team Roster</h2>
                <Card>
                    <Card.Body className="p-0">
                        <div className="table-responsive">
                            <Table className="mb-0">
                                <thead>
                                    <tr>
                                        <th>#</th>
                                        <th>Player Name</th>
                                        <th>Role</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {teamData?.roster?.length > 0 ? (
                                        teamData.roster.map((player, index) => (
                                            <tr key={index}>
                                                <td>{index + 1}</td>
                                                <td>{player.name}</td>
                                                <td>
                                                    <span className={`role-badge role-${player.role.toLowerCase().replace('-', '')}`}>
                                                        {player.role}
                                                    </span>
                                                </td>
                                            </tr>
                                        ))
                                    ) : (
                                        <tr>
                                            <td colSpan="3" className="text-center py-4">
                                                No roster data available
                                            </td>
                                        </tr>
                                    )}
                                </tbody>
                            </Table>
                        </div>
                    </Card.Body>
                </Card>
            </div>

            {error && (
                <Alert variant="info" className="mt-3">
                    Note: Displaying sample data. Team-specific predictions will be available once the season begins.
                </Alert>
            )}
        </Container>
    );
};

export default TeamDetail;
