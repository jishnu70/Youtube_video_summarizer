package repo

// go/internal/repo/summary.go

import (
	"context"
	"errors"

	db "github.com/jishnu70/Youtube_video_summarizer/internal/db"
	"github.com/jishnu70/Youtube_video_summarizer/internal/domain"
	"go.mongodb.org/mongo-driver/v2/bson"
	"go.mongodb.org/mongo-driver/v2/mongo"
	"go.mongodb.org/mongo-driver/v2/mongo/options"
)

type SummaryRepo struct {
	collection *mongo.Collection
}

func NewSummaryRepo(mongoDB *db.MongoDB, collectionName string) (*SummaryRepo, error) {
	if mongoDB == nil {
		return nil, errors.New("mongodb client is not initialized")
	}
	collection, err := mongoDB.Collection(collectionName)
	if err != nil {
		return nil, err
	}
	return &SummaryRepo{
		collection: collection,
	}, nil
}

func (r *SummaryRepo) EnsureIndex(ctx context.Context) error {
	indexModel := []mongo.IndexModel{
		{Keys: bson.D{
			{Key: "video_id", Value: 1},
			{Key: "created_at", Value: -1},
		}, Options: options.Index()},
		{Keys: bson.D{
			{Key: "video_url", Value: 1},
		}, Options: options.Index()},
	}
	_, err := r.collection.Indexes().CreateMany(ctx, indexModel)
	if err != nil {
		return err
	}
	return nil
}

func (r *SummaryRepo) Insert(ctx context.Context, summary *domain.Summary) (*domain.Summary, error) {
	if summary == nil {
		return nil, errors.New("summary is nil")
	}
	videoID, err := bson.ObjectIDFromHex(summary.VideoID)
	if err != nil {
		return nil, errors.New("invalid video ID")
	}
	summaryDBL := &db.SummaryDB{
		ID:        bson.NewObjectID(),
		VideoID:   videoID,
		VideoUrl:  summary.VideoUrl,
		Summary:   summary.Summary,
		ModelName: summary.ModelName,
		CreatedAt: summary.CreatedAt,
	}
	_, err = r.collection.InsertOne(ctx, summaryDBL)
	if err != nil {
		return nil, err
	}
	return summaryDBL.ToDomain(), nil
}

func (r *SummaryRepo) FindByID(ctx context.Context, id string) (*domain.Summary, error) {
	bsonID, err := bson.ObjectIDFromHex(id)
	if err != nil {
		return nil, errors.New("invalid summary ID")
	}
	filter := bson.D{{Key: "_id", Value: bsonID}}
	var summary db.SummaryDB
	err = r.collection.FindOne(ctx, filter).Decode(&summary)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, errors.New("summary not found")
		}
		return nil, err
	}
	return summary.ToDomain(), nil
}

func (r *SummaryRepo) FindByVideoID(ctx context.Context, videoID string) (*domain.Summary, error) {
	bsonVideoID, err := bson.ObjectIDFromHex(videoID)
	if err != nil {
		return nil, errors.New("invalid video ID")
	}
	filter := bson.D{{Key: "video_id", Value: bsonVideoID}}
	opts := options.FindOne().SetSort(bson.D{{Key: "created_at", Value: -1}})
	var summary db.SummaryDB
	err = r.collection.FindOne(ctx, filter, opts).Decode(&summary)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, errors.New("summary not found")
		}
		return nil, err
	}
	return summary.ToDomain(), nil
}

func (r *SummaryRepo) FindByVideoURL(ctx context.Context, videoURL string) (*domain.Summary, error) {
	filter := bson.D{{Key: "video_url", Value: videoURL}}
	opts := options.FindOne().SetSort(bson.D{{Key: "created_at", Value: -1}})
	var summary db.SummaryDB
	err := r.collection.FindOne(ctx, filter, opts).Decode(&summary)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, errors.New("summary not found")
		}
		return nil, err
	}
	return summary.ToDomain(), nil
}

func (r *SummaryRepo) FindAllByVideoID(
	ctx context.Context,
	videoID string,
	lastID string,
	limit int64,
) ([]*domain.Summary, error) {
	return r.FindAllSummaries(ctx, &videoID, lastID, limit)
}

func (r *SummaryRepo) FindAllSummaries(
	ctx context.Context,
	videoID *string,
	lastID string,
	limit int64,
) ([]*domain.Summary, error) {
	filter := bson.D{}
	if videoID != nil {
		bsonVideoID, err := bson.ObjectIDFromHex(*videoID)
		if err != nil {
			return nil, errors.New("invalid video ID")
		}
		filter = append(filter, bson.E{Key: "video_id", Value: bsonVideoID})
	}
	bsonLastID, err := bson.ObjectIDFromHex(lastID)
	if err != nil {
		return nil, errors.New("invalid last ID")
	}
	opts := options.Find().SetSort(bson.D{{Key: "created_at", Value: -1}}).SetLimit(limit)
	filter = append(filter, bson.E{Key: "_id", Value: bson.D{{Key: "$lt", Value: bsonLastID}}})
	cursor, err := r.collection.Find(ctx, filter, opts)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var domainSummaries []*domain.Summary

	for cursor.Next(ctx) {
		var summary db.SummaryDB
		if err := cursor.Decode(&summary); err != nil {
			return nil, err
		}
		domainSummaries = append(domainSummaries, summary.ToDomain())
	}

	if err := cursor.Err(); err != nil {
		return nil, err
	}

	return domainSummaries, nil
}
