package domain

import "errors"

// api/internal/domain/errors.go

// Defining all config errors
var (
	ErrConfigFileNotFound = errors.New("config file not found")
	ErrConfigFileRead     = errors.New("failed to read config file")
	ErrConfigParse        = errors.New("failed to parse config file")
	ErrConfigMissingField = errors.New("missing required config field")
)

// Defining all DB errors
var (
	ErrDBClientNotInitialized     = errors.New("DB client is nil")
	ErrDBDatabaseNotInitialized   = errors.New("DB database is nil")
	ErrDBCollectionNotInitialized = errors.New("DB collection is nil")
	ErrDBConnectionFailed         = errors.New("failed to connect to DB")
	ErrDBConnectionTimeout        = errors.New("DB connection timed out")
	ErrDBPingFailed               = errors.New("failed to ping DB")
	ErrDBDisconnectFailed         = errors.New("failed to disconnect from DB")
	ErrDBCollectionNotFound       = errors.New("DB collection not found")
	ErrDBInsertFailed             = errors.New("failed to insert document into DB")
	ErrDBFindFailed               = errors.New("failed to find document in DB")
	ErrDBNoDocuments              = errors.New("no documents found in DB")
	ErrDBIndexCreationFailed      = errors.New("failed to create index in DB")
	ErrDBInvalidObjectID          = errors.New("invalid ObjectID format")
)

// Defining all cache errors
var (
	ErrCacheClientNotInitialized = errors.New("cache client is nil")
	ErrCacheConnectionFailed     = errors.New("failed to connect to cache")
	ErrCacheConnectionTimeout    = errors.New("cache connection timed out")
	ErrCachePingFailed           = errors.New("failed to ping cache")
	ErrCacheDisconnectFailed     = errors.New("failed to disconnect from cache")
	ErrCacheKeyNotFound          = errors.New("cache key not found")
	ErrCacheSetFailed            = errors.New("failed to set cache value")
	ErrCacheKeyAlreadyExists     = errors.New("cache key already exists")
	ErrCacheGetFailed            = errors.New("failed to get cache value")
	ErrCacheDeleteFailed         = errors.New("failed to delete cache value")
)

// Defining all Repo errors
var (

	// Defining all SummaryRepo errors
	ErrSummaryRepoNotInitialized = errors.New("summary repo is nil")
	ErrSummaryNotFound           = errors.New("summary not found")

	// Defining all TaskRepo errors
	ErrTaskRepoNotInitialized = errors.New("task repo is nil")
	ErrTaskNotFound           = errors.New("task not found")

	// Defining all CacheRepo errors
	ErrCacheRepoNotInitialized = errors.New("cache repo is nil")
	ErrCacheMiss               = errors.New("cache miss")
)

// Defining all Service errors
var (
	// Defining all SummaryService errors
	ErrSummaryServiceNotInitialized = errors.New("summary service is nil")
	ErrVideoURLEmpty                = errors.New("video URL is empty")

	// Defining all TaskService errors
	ErrTaskServiceNotInitialized = errors.New("task service is nil")
	ErrTaskIDEmpty               = errors.New("task ID is empty")

	// Defining all CacheService errors
	ErrCacheServiceNotInitialized = errors.New("cache service is nil")
)
