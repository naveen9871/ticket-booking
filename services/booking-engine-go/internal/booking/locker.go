package booking

import (
	"context"
	"errors"
	"sync"
	"time"
)

type lockValue struct {
	owner     string
	expiresAt time.Time
}

type MemoryLocker struct {
	mu  sync.Mutex
	ttl time.Duration
	kv  map[string]lockValue
}

func NewMemoryLocker(ttl time.Duration) *MemoryLocker {
	return &MemoryLocker{ttl: ttl, kv: map[string]lockValue{}}
}

func (m *MemoryLocker) Lock(_ context.Context, key string, owner string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	now := time.Now().UTC()
	current, exists := m.kv[key]
	if exists && current.expiresAt.After(now) && current.owner != owner {
		return errors.New("lock already held")
	}
	m.kv[key] = lockValue{owner: owner, expiresAt: now.Add(m.ttl)}
	return nil
}

func (m *MemoryLocker) Unlock(_ context.Context, key string, owner string) error {
	m.mu.Lock()
	defer m.mu.Unlock()
	current, exists := m.kv[key]
	if exists && current.owner == owner {
		delete(m.kv, key)
	}
	return nil
}

func (m *MemoryLocker) ExpiresAt() time.Time {
	return time.Now().UTC().Add(m.ttl)
}

