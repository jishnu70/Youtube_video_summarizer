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
			return nil, domain.NewAppError(
				domain.DatabaseLayer,
				domain.CodeTimeout,
				domain.ErrDBConnectionTimeout,
				err,
			)
		}
		return nil, domain.NewAppError(
			domain.DatabaseLayer,
			domain.CodeConnectionError,
			domain.ErrDBConnectionFailed,
			err,
		)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 5*time.Second)
	defer cancel()

	if pingErr := client.Ping(ctx, nil); pingErr != nil {
		_ = client.Disconnect(ctx)
		return nil, domain.NewAppError(
			domain.DatabaseLayer,
			domain.CodeConnectionError,
			domain.ErrDBConnectionFailed,
			pingErr,
		)
	}
	database := client.Database(databaseName)

	return &MongoDB{
		client:   client,
		database: database,
	}, nil
}

func (m *MongoDB) Ping(ctx context.Context) error {
	// Implement a ping method to check the connection to MongoDB
	if err := m.client.Ping(ctx, nil); err != nil {
		if errors.Is(err, context.DeadlineExceeded) {
			return domain.NewAppError(
				domain.DatabaseLayer,
				domain.CodeTimeout,
				domain.ErrDBConnectionTimeout,
				err,
			)
		}
		return domain.NewAppError(
			domain.DatabaseLayer,
			domain.CodeConnectionError,
			domain.ErrDBPingFailed,
			err,
		)
	}
	return nil
}

func (m *MongoDB) Close(ctx context.Context) error {
	// Implement a method to close the MongoDB connection
	if err := m.client.Disconnect(ctx); err != nil {
		return domain.NewAppError(
			domain.DatabaseLayer,
			domain.CodeConnectionError,
			domain.ErrDBDisconnectFailed,
			err,
		)
	}
	return nil
}

func (m *MongoDB) Collection(collectionName string) *mongo.Collection {
	// Implement a method to get a collection from the MongoDB database
	return m.database.Collection(collectionName)
}
