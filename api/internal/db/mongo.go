package db

// api/internal/db/mongo.go

import (
	"context"
	"errors"
	"time"

	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type MongoDB struct {
	// Add fields for MongoDB connection, e.g., client, database, collection, etc.
	client   *mongo.Client
	database *mongo.Database
}

func New(uri, databaseName string) (*MongoDB, error) {
	// Initialize MongoDB connection here using the provided URI
	serverAPI := options.ServerAPI(options.ServerAPIVersion1)
	clientOptions := options.Client().ApplyURI(uri).SetServerAPIOptions(serverAPI).SetTimeout(5 * time.Second)

	client, err := mongo.Connect(clientOptions)
	if err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			return nil, domain.ErrDBConnectionTimeout
		}
		return nil, domain.ErrDBConnectionFailed
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if pingErr := client.Ping(ctx, nil); pingErr != nil {
		if err := client.Disconnect(ctx); err != nil {
			return nil, domain.ErrDBDisconnectFailed
		} // Disconnect the client if ping fails
		return nil, domain.ErrDBPingFailed
	}
	database := client.Database(databaseName)

	if database == nil {
		return nil, domain.ErrDBDatabaseNotInitialized
	}

	return &MongoDB{
		client:   client,
		database: database,
	}, nil
}

func (m *MongoDB) Ping(ctx context.Context) error {
	// Implement a ping method to check the connection to MongoDB
	if m.client == nil {
		return domain.ErrDBClientNotInitialized
	}
	return m.client.Ping(ctx, nil)
}

func (m *MongoDB) Close(ctx context.Context) error {
	// Implement a method to close the MongoDB connection
	if m.client == nil {
		return domain.ErrDBClientNotInitialized
	}
	return m.client.Disconnect(ctx)
}

func (m *MongoDB) Collection(collectionName string) (*mongo.Collection, error) {
	// Implement a method to get a collection from the MongoDB database
	if m.database == nil {
		return nil, domain.ErrDBDatabaseNotInitialized
	}
	return m.database.Collection(collectionName), nil
}
