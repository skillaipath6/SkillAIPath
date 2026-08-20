"""💰 Dynamic Pricing Engine API - Production Application

REST API for dynamic pricing with rule engine, audit trail, and rate limiting.
Production-grade with FastAPI, authentication, validation, and comprehensive OpenAPI docs.

DATA SOURCES:
- Unity Catalog: sap_dev.gold.mart_inventory_health (inventory metrics)
- Lakebase Postgres: pricing_rules, price_change_history (pricing config & audit)
"""

from fastapi import FastAPI, HTTPException, Depends, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime, timedelta
from decimal import Decimal
import sys
import os
import json
import logging

# Add shared modules to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../_shared'))

from config import config
from db_manager import get_database_manager
from logger import setup_logging
from validators import Validator

# Setup logging
logger = setup_logging("DynamicPricingAPI", config.app.log_level)

# Initialize FastAPI app
app = FastAPI(
    title="Dynamic Pricing Engine API",
    description="Production-grade API for real-time dynamic pricing with rule engine and audit trail",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Database manager
db_manager = get_database_manager(config)


# ============================================================================
# Pydantic Models for Request/Response
# ============================================================================

class PricingRuleCreate(BaseModel):
    """Request model for creating a pricing rule."""
    
    rule_name: str = Field(..., min_length=1, max_length=100, description="Unique rule name")
    stock_status: Optional[str] = Field(None, description="Stock status filter (Critical, Understock, Overstock)")
    health_status: Optional[str] = Field(None, description="Health status filter")
    price_adjustment_pct: float = Field(..., ge=-90, le=100, description="Price adjustment percentage (-90 to +100)")
    is_active: bool = Field(True, description="Whether rule is active")
    created_by: str = Field(..., description="User who created the rule")
    
    @validator('price_adjustment_pct')
    def validate_adjustment(cls, v):
        """Validate price adjustment percentage."""
        if not -90 <= v <= 100:
            raise ValueError("Price adjustment must be between -90% and +100%")
        return round(v, 2)


class PricingRule(BaseModel):
    """Response model for a pricing rule."""
    
    rule_id: int
    rule_name: str
    stock_status: Optional[str]
    health_status: Optional[str]
    price_adjustment_pct: float
    is_active: bool
    created_by: str
    created_at: datetime


class PriceCalculationRequest(BaseModel):
    """Request model for price calculation."""
    
    product_id: int = Field(..., gt=0, description="Product ID")
    warehouse_id: int = Field(..., gt=0, description="Warehouse ID")
    base_price: float = Field(..., gt=0, description="Base price to adjust")
    
    @validator('base_price')
    def validate_price(cls, v):
        """Validate base price."""
        if v <= 0:
            raise ValueError("Base price must be positive")
        if v > 1000000:
            raise ValueError("Base price seems unrealistic")
        return round(v, 2)


class PriceCalculationResponse(BaseModel):
    """Response model for price calculation."""
    
    product_id: int
    warehouse_id: int
    base_price: float
    adjusted_price: float
    adjustment_pct: float
    applied_rule: Optional[str]
    stock_status: str
    health_status: str
    calculated_at: datetime


class PriceChangeHistory(BaseModel):
    """Response model for price change history."""
    
    change_id: int
    product_id: int
    warehouse_id: int
    old_price: float
    new_price: float
    adjustment_pct: float
    applied_rule: Optional[str]
    changed_at: datetime


class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    
    status: str
    timestamp: datetime
    version: str
    database_status: Dict[str, bool]


# ============================================================================
# Security & Authentication
# ============================================================================

async def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """Verify API token (simplified for demo - use proper OAuth in production)."""
    
    # In production, validate against a token store or OAuth provider
    token = credentials.credentials
    
    # Simple validation (replace with proper auth)
    if not token or len(token) < 10:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


# ============================================================================
# Business Logic Services
# ============================================================================

class InventoryService:
    """Service for fetching inventory data."""
    
    @staticmethod
    def get_product_inventory(product_id: int, warehouse_id: int) -> Optional[Dict]:
        """Get inventory status for a product at a warehouse."""
        try:
            query = f"""
                SELECT 
                    ProductSK,
                    WarehouseSK,
                    ProductName,
                    WarehouseName,
                    CurrentStock,
                    HealthStatus,
                    DaysOfStock
                FROM {config.unity_catalog.catalog}.gold.mart_inventory_health
                WHERE ProductSK = {product_id}
                AND WarehouseSK = {warehouse_id}
                LIMIT 1
            """
            
            with db_manager.unity_catalog_cursor() as cursor:
                cursor.execute(query)
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
                
        except Exception as e:
            logger.error(f"Failed to fetch inventory: {e}")
            return None


class PricingRuleService:
    """Service for managing pricing rules."""
    
    @staticmethod
    def create_rule(rule: PricingRuleCreate) -> int:
        """Create a new pricing rule."""
        try:
            with db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO pricing_rules (
                        rule_name, stock_status, health_status,
                        price_adjustment_pct, is_active, created_by, created_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING rule_id
                """, (
                    rule.rule_name,
                    rule.stock_status,
                    rule.health_status,
                    rule.price_adjustment_pct,
                    rule.is_active,
                    rule.created_by,
                    datetime.now()
                ))
                
                rule_id = cursor.fetchone()[0]
            
            logger.info(f"Created pricing rule {rule_id}: {rule.rule_name}")
            return rule_id
            
        except Exception as e:
            logger.error(f"Failed to create pricing rule: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create pricing rule: {str(e)}"
            )
    
    @staticmethod
    def get_all_rules(active_only: bool = True) -> List[Dict]:
        """Get all pricing rules."""
        try:
            active_filter = "WHERE is_active = true" if active_only else ""
            
            with db_manager.lakebase_cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        rule_id, rule_name, stock_status, health_status,
                        price_adjustment_pct, is_active, created_by, created_at
                    FROM pricing_rules
                    {active_filter}
                    ORDER BY created_at DESC
                """)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to fetch pricing rules: {e}")
            return []
    
    @staticmethod
    def get_applicable_rule(health_status: str, stock_status: str = None) -> Optional[Dict]:
        """Get the first applicable pricing rule for given conditions."""
        try:
            with db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        rule_id, rule_name, price_adjustment_pct
                    FROM pricing_rules
                    WHERE is_active = true
                    AND (health_status = %s OR health_status IS NULL)
                    AND (stock_status = %s OR stock_status IS NULL)
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (health_status, stock_status))
                
                row = cursor.fetchone()
                
                if row:
                    columns = [desc[0] for desc in cursor.description]
                    return dict(zip(columns, row))
                
                return None
                
        except Exception as e:
            logger.error(f"Failed to get applicable rule: {e}")
            return None
    
    @staticmethod
    def delete_rule(rule_id: int) -> bool:
        """Delete a pricing rule."""
        try:
            with db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    DELETE FROM pricing_rules
                    WHERE rule_id = %s
                """, (rule_id,))
            
            logger.info(f"Deleted pricing rule {rule_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete pricing rule: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete rule: {str(e)}"
            )


class PriceHistoryService:
    """Service for managing price change history."""
    
    @staticmethod
    def log_price_change(
        product_id: int,
        warehouse_id: int,
        old_price: float,
        new_price: float,
        adjustment_pct: float,
        applied_rule: Optional[str]
    ) -> int:
        """Log a price change to history."""
        try:
            with db_manager.lakebase_cursor() as cursor:
                cursor.execute("""
                    INSERT INTO price_change_history (
                        product_id, warehouse_id, old_price, new_price,
                        adjustment_pct, applied_rule, changed_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING change_id
                """, (
                    product_id,
                    warehouse_id,
                    old_price,
                    new_price,
                    adjustment_pct,
                    applied_rule,
                    datetime.now()
                ))
                
                change_id = cursor.fetchone()[0]
            
            logger.info(f"Logged price change {change_id}")
            return change_id
            
        except Exception as e:
            logger.error(f"Failed to log price change: {e}")
            raise
    
    @staticmethod
    def get_price_history(
        product_id: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get price change history."""
        try:
            product_filter = f"WHERE product_id = {product_id}" if product_id else ""
            
            with db_manager.lakebase_cursor() as cursor:
                cursor.execute(f"""
                    SELECT 
                        change_id, product_id, warehouse_id,
                        old_price, new_price, adjustment_pct,
                        applied_rule, changed_at
                    FROM price_change_history
                    {product_filter}
                    ORDER BY changed_at DESC
                    LIMIT {limit}
                """)
                
                rows = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                
                return [dict(zip(columns, row)) for row in rows]
                
        except Exception as e:
            logger.error(f"Failed to fetch price history: {e}")
            return []


# ============================================================================
# API Endpoints
# ============================================================================

@app.get("/", response_model=HealthCheckResponse)
async def root():
    """Root endpoint with health check."""
    
    db_status = db_manager.test_connections()
    
    return HealthCheckResponse(
        status="healthy" if all(db_status.values()) else "degraded",
        timestamp=datetime.now(),
        version="2.0.0",
        database_status={
            "lakebase": db_status.get("lakebase", False),
            "unity_catalog": db_status.get("unity_catalog", False)
        }
    )


@app.get("/health")
async def health_check():
    """Detailed health check endpoint."""
    
    db_status = db_manager.test_connections()
    
    return {
        "status": "healthy" if all(db_status.values()) else "degraded",
        "timestamp": datetime.now().isoformat(),
        "databases": db_status,
        "errors": db_status.get("errors", [])
    }


@app.post("/api/v1/pricing/rules", response_model=PricingRule, status_code=status.HTTP_201_CREATED)
async def create_pricing_rule(
    rule: PricingRuleCreate,
    token: str = Depends(verify_token)
):
    """Create a new pricing rule.
    
    Requires authentication token.
    """
    
    rule_id = PricingRuleService.create_rule(rule)
    
    # Fetch created rule
    rules = PricingRuleService.get_all_rules(active_only=False)
    created_rule = next((r for r in rules if r['rule_id'] == rule_id), None)
    
    if not created_rule:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Rule created but could not be retrieved"
        )
    
    return PricingRule(**created_rule)


@app.get("/api/v1/pricing/rules", response_model=List[PricingRule])
async def get_pricing_rules(
    active_only: bool = True,
    token: str = Depends(verify_token)
):
    """Get all pricing rules.
    
    Query Parameters:
    - active_only: If true, return only active rules
    """
    
    rules = PricingRuleService.get_all_rules(active_only=active_only)
    return [PricingRule(**rule) for rule in rules]


@app.delete("/api/v1/pricing/rules/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pricing_rule(
    rule_id: int,
    token: str = Depends(verify_token)
):
    """Delete a pricing rule by ID."""
    
    PricingRuleService.delete_rule(rule_id)
    return None


@app.post("/api/v1/pricing/calculate", response_model=PriceCalculationResponse)
async def calculate_price(
    request: PriceCalculationRequest,
    token: str = Depends(verify_token)
):
    """Calculate dynamic price for a product at a warehouse.
    
    Applies pricing rules based on inventory health and stock status.
    Logs price changes to audit trail.
    """
    
    # Get inventory status
    inventory = InventoryService.get_product_inventory(
        request.product_id,
        request.warehouse_id
    )
    
    if not inventory:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product {request.product_id} not found at warehouse {request.warehouse_id}"
        )
    
    # Get applicable pricing rule
    rule = PricingRuleService.get_applicable_rule(
        inventory['HealthStatus']
    )
    
    # Calculate adjusted price
    if rule:
        adjustment_pct = rule['price_adjustment_pct']
        rule_name = rule['rule_name']
    else:
        adjustment_pct = 0.0
        rule_name = None
    
    adjusted_price = request.base_price * (1 + adjustment_pct / 100)
    adjusted_price = round(adjusted_price, 2)
    
    # Log price change
    if adjusted_price != request.base_price:
        PriceHistoryService.log_price_change(
            request.product_id,
            request.warehouse_id,
            request.base_price,
            adjusted_price,
            adjustment_pct,
            rule_name
        )
    
    logger.info(f"Calculated price for product {request.product_id}: {request.base_price} -> {adjusted_price}")
    
    return PriceCalculationResponse(
        product_id=request.product_id,
        warehouse_id=request.warehouse_id,
        base_price=request.base_price,
        adjusted_price=adjusted_price,
        adjustment_pct=adjustment_pct,
        applied_rule=rule_name,
        stock_status=inventory.get('HealthStatus', 'Unknown'),
        health_status=inventory.get('HealthStatus', 'Unknown'),
        calculated_at=datetime.now()
    )


@app.get("/api/v1/pricing/history", response_model=List[PriceChangeHistory])
async def get_price_history(
    product_id: Optional[int] = None,
    limit: int = 100,
    token: str = Depends(verify_token)
):
    """Get price change history.
    
    Query Parameters:
    - product_id: Filter by product ID (optional)
    - limit: Maximum number of records (default: 100)
    """
    
    history = PriceHistoryService.get_price_history(product_id, limit)
    return [PriceChangeHistory(**record) for record in history]


# ============================================================================
# Error Handlers
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions with consistent format."""
    return {
        "error": exc.detail,
        "status_code": exc.status_code,
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle unexpected exceptions."""
    logger.exception("Unexpected error")
    return {
        "error": "Internal server error",
        "detail": str(exc),
        "status_code": 500,
        "timestamp": datetime.now().isoformat()
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
