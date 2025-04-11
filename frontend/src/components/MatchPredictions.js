import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Table, Tabs, Tab, Form } from 'react-bootstrap';
import { getMatchPredictions, getMatches } from '../api';

const MatchPredictions = () => {
    const [matches, setMatches] = useState([]);
    const [selectedMatch, setSelectedMatch] = useState(null);
    const [predictions, setPredictions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    useEffect(() => {
        loadMatches();
    }, []);

    const loadMatches = async () => {
        try {
            const data = await getMatches();
            setMatches(data);
        } catch (err) {
            setError('Failed to load matches');
            console.error(err);
        }
    };

    const handleMatchChange = async (matchNo) => {
        setLoading(true);
        setError(null);
        try {
            const data = await getMatchPredictions(matchNo);
            setSelectedMatch(data.match);
            setPredictions(data.predictions);
        } catch (err) {
            setError('Failed to load predictions');
            console.error(err);
        }
        setLoading(false);
    };

    const renderPredictionTable = (players) => (
        <Table striped bordered hover responsive>
            <thead>
                <tr>
                    <th>Player</th>
                    <th>Role</th>
                    <th>Team</th>
                    <th>Predicted Runs</th>
                    <th>Predicted Wickets</th>
                    <th>Strike Rate</th>
                    <th>Economy Rate</th>
                </tr>
            </thead>
            <tbody>
                {players.map((pred, index) => (
                    <tr key={index}>
                        <td>{pred.player.name}</td>
                        <td>{pred.player.role}</td>
                        <td>{pred.team}</td>
                        <td>{pred.prediction.batting.value}</td>
                        <td>{pred.prediction.bowling.value}</td>
                        <td>{pred.prediction.batting.strike_rate}</td>
                        <td>{pred.prediction.bowling.economy_rate}</td>
                    </tr>
                ))}
            </tbody>
        </Table>
    );

    return (
        <Container fluid className="py-4">
            <Row className="mb-4">
                <Col>
                    <Card>
                        <Card.Body>
                            <Form.Group>
                                <Form.Label>Select Match</Form.Label>
                                <Form.Control
                                    as="select"
                                    onChange={(e) => handleMatchChange(e.target.value)}
                                >
                                    <option value="">Choose a match...</option>
                                    {matches.map((match) => (
                                        <option key={match.match_no} value={match.match_no}>
                                            Match {match.match_no}: {match.team1} vs {match.team2} ({match.date})
                                        </option>
                                    ))}
                                </Form.Control>
                            </Form.Group>
                        </Card.Body>
                    </Card>
                </Col>
            </Row>

            {error && (
                <Row className="mb-4">
                    <Col>
                        <div className="alert alert-danger">{error}</div>
                    </Col>
                </Row>
            )}

            {loading && (
                <Row className="mb-4">
                    <Col>
                        <div className="text-center">Loading predictions...</div>
                    </Col>
                </Row>
            )}

            {selectedMatch && predictions.length > 0 && (
                <Row>
                    <Col>
                        <Card className="mb-4">
                            <Card.Body>
                                <h4>Match Details</h4>
                                <p>
                                    <strong>Match {selectedMatch.match_no}:</strong> {selectedMatch.team1} vs {selectedMatch.team2}
                                </p>
                                <p>
                                    <strong>Date:</strong> {selectedMatch.date} at {selectedMatch.time}
                                </p>
                                <p>
                                    <strong>Venue:</strong> {selectedMatch.venue}
                                </p>
                            </Card.Body>
                        </Card>

                        <Tabs defaultActiveKey="all" className="mb-4">
                            <Tab eventKey="all" title="All Players">
                                {renderPredictionTable(predictions)}
                            </Tab>
                            <Tab eventKey="team1" title={selectedMatch.team1}>
                                {renderPredictionTable(
                                    predictions.filter(p => p.team === selectedMatch.team1)
                                )}
                            </Tab>
                            <Tab eventKey="team2" title={selectedMatch.team2}>
                                {renderPredictionTable(
                                    predictions.filter(p => p.team === selectedMatch.team2)
                                )}
                            </Tab>
                        </Tabs>
                    </Col>
                </Row>
            )}
        </Container>
    );
};

export default MatchPredictions; 