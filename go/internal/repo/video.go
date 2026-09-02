package repo

// go/internal/repo/video.go

import (
	"context"
	"errors"
	"strings"
	"time"

	db "github.com/jishnu70/Youtube_video_summarizer/internal/db"
	domain "github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

func strToObjectID(id string) (bson.ObjectID, error) {
	objectID, err := bson.ObjectIDFromHex(id)
	if err != nil {
		return bson.ObjectID{}, errors.New("invalid ObjectID format")
	}
	return objectID, nil
}

type VideoRepo struct {
	collection *mongo.Collection
}

func NewVideoRepo(mongoDB *db.MongoDB, collectionName string) (*VideoRepo, error) {
	// Implement the logic to get the collection from the MongoDB client
	// Load collectionName from the .env file through congif.go or from the main.go
	// Do not hardcode the collection name here, as it may change in the future.
	if mongoDB == nil {
		return nil, errors.New("mongodb client is not initialized")
	}
	collection, err := mongoDB.Collection(collectionName)
	if err != nil {
		return nil, err
	}
	return &VideoRepo{
		collection: collection,
	}, nil
}

func (r *VideoRepo) EnsureIndex(ctx context.Context) error {
	// Implement the logic to create indexes for the video collection
	indexModel := []mongo.IndexModel{
		{Keys: bson.D{{Key: "video_url", Value: 1}}, Options: options.Index().SetUnique(true)},
	}
	_, err := r.collection.Indexes().CreateMany(ctx, indexModel)
	if err != nil {
		return err
	}
	return nil
}

func (r *VideoRepo) Insert(ctx context.Context, video *domain.Video) (*domain.Video, error) {
	// Implement the logic to insert a video document into the collection
	if video == nil {
		return nil, errors.New("video is nil")
	}

	videoDB := &db.VideoDB{
		ID:         bson.NewObjectID(),
		VideoURL:   video.VideoURL,
		Transcript: video.Transcript,
		CreatedAt:  video.CreatedAt,
		UpdatedAt:  video.UpdatedAt,
	}

	insertedResult, err := r.collection.InsertOne(ctx, videoDB)
	if err != nil {
		return nil, err
	}
	// Set the inserted ID to the video struct
	videoDB.ID = insertedResult.InsertedID.(bson.ObjectID)
	return videoDB.ToDomain(), nil
}

func (r *VideoRepo) findByKey(
	ctx context.Context,
	key string,
	value any,
	result *db.VideoDB,
) error {
	// Implement the logic to find a video document by a specific key-value pair
	filter := bson.D{{Key: key, Value: value}}
	err := r.collection.FindOne(ctx, filter).Decode(result)

	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return domain.ErrVideoNotFound
		}
		return err
	}
	return nil
}

func (r *VideoRepo) FindByURL(ctx context.Context, video_url string) (*domain.Video, error) {
	// Implement the logic to find a video document by its URL
	if strings.TrimSpace(video_url) == "" {
		return nil, errors.New("video URL is empty")
	}
	var obj db.VideoDB

	if err := r.findByKey(ctx, "video_url", video_url, &obj); err != nil {
		return nil, err
	}
	return obj.ToDomain(), nil
}

func (r *VideoRepo) FindByID(ctx context.Context, id string) (*domain.Video, error) {
	// Implement the logic to find a video document by its ID
	_id, idErr := strToObjectID(id)
	if idErr != nil {
		return nil, idErr
	}
	var obj db.VideoDB

	if err := r.findByKey(ctx, "_id", _id, &obj); err != nil {
		return nil, err
	}
	return obj.ToDomain(), nil
}

func (r *VideoRepo) Update(ctx context.Context, id string, update map[string]any) error {
	// Implement the logic to update a video document by its ID
	_id, idErr := strToObjectID(id)
	if idErr != nil {
		return idErr
	}
	bsonUpdate := bson.D{}
	for k, v := range update {
		bsonUpdate = append(bsonUpdate, bson.E{Key: k, Value: v})
	}
	bsonUpdate = append(bsonUpdate, bson.E{Key: "updated_at", Value: time.Now().UTC()})
	result, updataErr := r.collection.UpdateOne(
		ctx,
		bson.D{{Key: "_id", Value: _id}},
		bson.D{{Key: "$set", Value: bsonUpdate}},
	)
	if updataErr != nil {
		return updataErr
	}
	if result.MatchedCount == 0 {
		return domain.ErrVideoNotFound
	}
	return nil
}

// Delete is not required.
