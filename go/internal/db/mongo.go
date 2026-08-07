package db

// go/internal/db/mongo.go

import (
	"context"
	"errors"
	"time"

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
		return nil, err
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if pingErr := client.Ping(ctx, nil); pingErr != nil {
		if err := client.Disconnect(ctx); err != nil {
			return nil, errors.New("failed to disconnect client after ping failure: " + err.Error())
		} // Disconnect the client if ping fails
		return nil, pingErr
	}

	database := client.Database(databaseName)

	if database == nil {
		return nil, errors.New("failed to get database")
	}

	return &MongoDB{
		client:   client,
		database: database,
	}, nil
}

func (m *MongoDB) Ping(ctx context.Context) error {
	// Implement a ping method to check the connection to MongoDB
	if m.client == nil {
		return errors.New("mongodb client is not initialized")
	}
	return m.client.Ping(ctx, nil)
}

func (m *MongoDB) Close(ctx context.Context) error {
	// Implement a method to close the MongoDB connection
	if m.client == nil {
		return nil
	}
	return m.client.Disconnect(ctx)
}

func (m *MongoDB) IsConnected(ctx context.Context) bool {
	// Implement a method to check if the MongoDB client is connected
	if m.client == nil {
		return false
	}
	if err := m.client.Ping(ctx, nil); err != nil {
		return false
	}
	return true
}

func (m *MongoDB) Client() *mongo.Client {
	// Implement a method to get the MongoDB client
	return m.client
}

func (m *MongoDB) Database() *mongo.Database {
	// Implement a method to get the MongoDB database
	return m.database
}

func (m *MongoDB) Collection(collectionName string) (*mongo.Collection, error) {
	// Implement a method to get a collection from the MongoDB database
	if m.database == nil {
		return nil, errors.New("mongodb database is not initialized")
	}
	return m.database.Collection(collectionName), nil
}
