CREATE TABLE votes (
    id SERIAL PRIMARY KEY,
    candidate VARCHAR(100),
    constituency VARCHAR(100),
    vote_time TIMESTAMP
);