# V2 Multi-Rate Limiter - Progress Checklist

## Phase 1: Core Model Updates
- [x] Update `RateLimiterMode` enum → `RateLimiterType` with expanded values (RPM, RPD, TPM, TPD, ITPM, OTPM, CONCURRENT)
- [x] Create `RateLimiterConfig` model for individual limiter configuration
- [x] Update `ModelConfig` to support `rate_limiters: List[RateLimiterConfig]`
- [x] Add backward compatibility for legacy `rate_limit` / `rate_limiter_mode` fields
- [x] Add token estimation fields to `QueueRequest` (`estimated_input_tokens`, `estimated_output_tokens`)
- [x] Add actual token fields to `QueueRequest` (`actual_input_tokens`, `actual_output_tokens`)
- [x] Add token usage fields to `QueueResponse` (`input_tokens_used`, `output_tokens_used`)

## Phase 2: Rate Limiter Refactoring
- [x] Create `rate_limiters/` module directory structure
- [x] Implement `BaseRateLimiter` abstract base class in `base.py`
- [x] Implement `RequestRateLimiter` for RPM/RPD in `request_limiter.py`
- [x] Implement `TokenRateLimiter` for TPM/TPD/ITPM/OTPM in `token_limiter.py`
- [x] Implement `ConcurrentRateLimiter` in `concurrent_limiter.py`
- [x] Implement `RateLimiterChain` in `chain.py`
- [x] Implement factory function to create limiters from config in `factory.py`
- [x] Create `rate_limiters/__init__.py` with exports
- [x] Update main `rate_limiter.py` for backward compatibility (re-export legacy class)

## Phase 3: Queue Integration
- [x] Update `Queue.__init__` to accept `RateLimiterChain` instead of single limiter
- [x] Update `Queue._process_queue` to use chain's `acquire_all` / `release_all`
- [x] Pass request to chain for token-aware limiting
- [x] Implement `Queue.update_token_usage` method
- [x] Track request token usage for adjustment after completion

## Phase 4: Manager Updates
- [x] Update `register_queue` to handle new `ModelConfig` with multiple rate limiters
- [x] Implement `update_token_usage` method for external token reporting
- [x] Update `get_queue_info` to return all rate limiter statuses
- [x] Maintain backward compatibility with legacy single-limiter config

## Phase 5: API Documentation
- [x] Create `docs/api.md`
- [x] Document `QueueManager` and `Queue` classes
- [x] Document `ModelConfig` and `RateLimiterConfig`
- [x] Document `RateLimiterType` and `QueueRequest`/`QueueResponse`

## Phase 6: Testing
- [ ] Add tests for `RateLimiterType` enum
- [ ] Add tests for `RateLimiterConfig` model
- [ ] Add tests for backward compatible `ModelConfig`
- [ ] Add tests for `RequestRateLimiter` (RPM/RPD)
- [ ] Add tests for `TokenRateLimiter` (TPM/TPD/ITPM/OTPM)
- [ ] Add tests for `ConcurrentRateLimiter`
- [ ] Create `test_rate_limiter_chain.py` with chain tests
- [ ] Update `test_queue.py` for multi-limiter integration
- [ ] Add tests for `update_token_usage` in queue
- [ ] Update `test_manager.py` for new `ModelConfig`
- [ ] Test backward compatibility with V1 API

## Phase 7: Documentation
- [x] Update `README.md` with V2 features
- [x] Add migration guide from V1 to V2
- [x] Update API reference documentation
- [x] Create new examples for multi-rate limiter usage
- [x] Update `CHANGELOG.md` for V2 release

## Post-Implementation
- [x] Run full test suite and verify all pass
- [x] Manual testing with sample scripts
- [x] Code review and cleanup
- [x] Update version number for V2 release
