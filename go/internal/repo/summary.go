package repo

// go/internal/repo/summary.go

import (
	"context"
	"errors"

	db "github.com/jishnu70/Youtube_video_summarizer/internal/db"
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

func (r *SummaryRepo) Insert(ctx context.Context, summary *db.SummaryDB) (*db.SummaryDB, error) {
	// Implement the logic to insert a summary document into the collection
	if summary == nil {
		return nil, errors.New("summary is nil")
	}
	filter := bson.D{{Key: "video_id", Value: summary.VideoID}}
	insertSummary := bson.M{
		"$push":        bson.M{"summaries": summary.Summary},
		"$setOnInsert": bson.M{"video_url": summary.VideoID},
	}
	opts := options.UpdateOne().SetUpsert(true)
	result, err := r.collection.UpdateOne(ctx, filter, insertSummary, opts)
	if err != nil {
		return nil, err
	}
	var resultID bson.ObjectID
	if result.UpsertedCount > 0 {
		if id, ok := result.UpsertedID.(bson.ObjectID); ok {
			resultID = id
		} else {
			return nil, errors.New("failed to get upserted ID")
		}
	} else {
		existing, err := r.FindByVideoID(ctx, summary.VideoID)
		if err != nil {
			return nil, err
		}
		resultID = existing.ID
	}
	return &db.SummaryDB{
		ID:       resultID,
		VideoID:  summary.VideoID,
		VideoUrl: summary.VideoUrl,
		Summary:  summary.Summary,
	}, nil
}

// findPipeline is a helper function that performs an aggregation query on the summary collection.
// It takes a context and a filter as input, and returns the first matching summary document.
// The aggregation pipeline sorts the summaries by created_at in descending order
// and projects the latest summary.
func (r *SummaryRepo) findPipeline(ctx context.Context, filter bson.D) (*db.SummaryDB, error) {
	pipeline := mongo.Pipeline{
		{{Key: "$match", Value: filter}},
		{{Key: "$project", Value: bson.M{
			"_id":       1,
			"video_id":  1,
			"video_url": 1,
			"summaryObject": bson.M{
				"$arrayElemAt": []any{
					bson.M{
						"$sortArray": bson.M{
							"input":  "$summaries",
							"sortBy": bson.M{"created_at": -1},
						},
					},
					0,
				},
			},
		}}},
	}

	cursor, err := r.collection.Aggregate(ctx, pipeline)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var summaries []db.SummaryDB
	if err = cursor.All(ctx, &summaries); err != nil {
		return nil, err
	}
	if len(summaries) == 0 {
		return nil, errors.New("no summaries found")
	}
	return &summaries[0], nil
}

func (r *SummaryRepo) FindByID(ctx context.Context, id bson.ObjectID) (*db.SummaryDB, error) {
	filter := bson.D{{Key: "_id", Value: id}}
	return r.findPipeline(ctx, filter)
}

func (r *SummaryRepo) FindByVideoID(ctx context.Context, videoID bson.ObjectID) (*db.SummaryDB, error) {
	filter := bson.D{{Key: "video_id", Value: videoID}}
	return r.findPipeline(ctx, filter)
}

func (r *SummaryRepo) FindByVideoURL(ctx context.Context, videoURL string) (*db.SummaryDB, error) {
	filter := bson.D{{Key: "video_url", Value: videoURL}}
	return r.findPipeline(ctx, filter)
}

// GetVideoCursor retrieves a paginated list of summaries from the summary collection.
// It takes a context, an optional lastID for pagination, and a pageLimit for the number of summaries to retrieve.
// If lastID is provided, it fetches summaries with IDs greater than lastID; otherwise, it fetches from the beginning.
// The results are sorted by ID in ascending order.
func (r *SummaryRepo) GetVideoCursor(
	ctx context.Context,
	lastID *bson.ObjectID,
	pageLimit int64,
) ([]db.SummaryDBList, error) {
	if pageLimit < 1 {
		pageLimit = 10
	}
	filter := bson.D{}
	if lastID != nil {
		filter = bson.D{{Key: "_id", Value: bson.D{{Key: "$gt", Value: *lastID}}}}
	} else {
		filter = bson.D{}
	}
	opt := options.Find().SetLimit(pageLimit).SetSort(bson.D{{Key: "_id", Value: 1}})
	cursor, err := r.collection.Find(ctx, filter, opt)
	if err != nil {
		return nil, err
	}
	defer cursor.Close(ctx)

	var summaries []db.SummaryDBList
	if err = cursor.All(ctx, &summaries); err != nil {
		return nil, err
	}
	if len(summaries) == 0 {
		return nil, errors.New("no summaries found")
	}
	return summaries, nil
}

func (r *SummaryRepo) GetSingleVideoWithPaginatedSummaries(
	ctx context.Context,
	videoID bson.ObjectID,
	lastSeenIndex int64,
	pageLimit int64,
) (*db.SummaryDBList, error) {
	if lastSeenIndex < 0 {
		lastSeenIndex = 0
	}
	if pageLimit < 1 {
		pageLimit = 10
	}
	filter := bson.D{{Key: "video_id", Value: videoID}}

	projections := bson.M{
		"summaries": bson.M{
			"$slice": []int64{lastSeenIndex, pageLimit},
		},
	}
	opts := options.FindOne().SetProjection(projections)
	var summary db.SummaryDBList
	err := r.collection.FindOne(ctx, filter, opts).Decode(&summary)
	if err != nil {
		if errors.Is(err, mongo.ErrNoDocuments) {
			return nil, errors.New("no summaries found for the given video ID")
		}
		return nil, err
	}
	return &summary, nil
}
