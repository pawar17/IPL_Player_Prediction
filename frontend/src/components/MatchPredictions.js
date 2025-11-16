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
        <Container>
            <div className="mb-5">
                <h1 className="display-5 mb-3">Match Predictions</h1>
                <p className="lead">Select a match to view player performance predictions</p>
            </div>

            <Row className="mb-4">
                <Col>
                    <Card>
                        <Card.Body className="p-4">
                            <Form.Group>
                                <Form.Label className="mb-3">
                                    Select Match
                                </Form.Label>
                                <Form.Control
                                    as="select"
                                    onChange={(e) => handleMatchChange(e.target.value)}
                                    className="form-select-lg"
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
                        <div className="text-center py-5">
                            <div className="spinner-border" role="status">
                                <span className="visually-hidden">Loading...</span>
                            </div>
                            <p className="mt-3">Loading predictions...</p>
                        </div>
                    </Col>
                </Row>
            )}

            {selectedMatch && predictions.length > 0 && (
                <Row>
                    <Col>
                        <Card className="mb-4">
                            <Card.Body className="p-4 bg-light">
                                <h4 className="mb-4">Match Details</h4>
                                <Row>
                                    <Col md={6} className="mb-3">
                                        <div className="detail-item p-3 bg-white rounded">
                                            <strong className="d-block mb-1">Teams</strong>
                                            <span className="fs-5">{selectedMatch.team1} vs {selectedMatch.team2}</span>
                                        </div>
                                    </Col>
                                    <Col md={3} className="mb-3">
                                        <div className="detail-item p-3 bg-white rounded">
                                            <strong className="d-block mb-1">Date</strong>
                                            <span>{selectedMatch.date}</span>
                                        </div>
                                    </Col>
                                    <Col md={3} className="mb-3">
                                        <div className="detail-item p-3 bg-white rounded">
                                            <strong className="d-block mb-1">Time</strong>
                                            <span>{selectedMatch.time}</span>
                                        </div>
                                    </Col>
                                    <Col md={12}>
                                        <div className="detail-item p-3 bg-white rounded">
                                            <strong className="d-block mb-1">Venue</strong>
                                            <span>{selectedMatch.venue}</span>
                                        </div>
                                    </Col>
                                </Row>
                            </Card.Body>
                        </Card>

                        <Card className="prediction-section">
                            <Card.Body className="p-0">
                                <div className="p-4 border-bottom">
                                    <h4 className="mb-0">Player Predictions</h4>
                                </div>
                                <Tabs defaultActiveKey="all" className="px-4 pt-3">
                                    <Tab eventKey="all" title={`All Players (${predictions.length})`}>
                                        <div className="p-3">
                                            {renderPredictionTable(predictions)}
                                        </div>
                                    </Tab>
                                    <Tab eventKey="team1" title={selectedMatch.team1}>
                                        <div className="p-3">
                                            {renderPredictionTable(
                                                predictions.filter(p => p.team === selectedMatch.team1)
                                            )}
                                        </div>
                                    </Tab>
                                    <Tab eventKey="team2" title={selectedMatch.team2}>
                                        <div className="p-3">
                                            {renderPredictionTable(
                                                predictions.filter(p => p.team === selectedMatch.team2)
                                            )}
                                        </div>
                                    </Tab>
                                </Tabs>
                            </Card.Body>
                        </Card>
                    </Col>
                </Row>
            )}
        </Container>
    );
};

export default MatchPredictions; 