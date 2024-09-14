from sqlalchemy import false, or_
from app.mixins.commons import DateRange
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql.elements import and_
from sqlalchemy.sql.functions import func
from app.utils.enums import ActionStatus
from app.config import database as db
from typing import Any, Generator
from pydantic.main import BaseModel

from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException


def get_db() -> Generator[Any, Any, Any]:
    dbase = db.SessionLocal()

    try:
        yield dbase
    finally:
        dbase.close()


class CrudUtil:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def create_model(
        self, model_to_create: Any, create: BaseModel, autocommit: bool = True
    ) -> Any:
        try:
            columns: set[str] = set(model_to_create.__table__.c.keys())
            create_columns: set[str] = set(create.model_dump().keys())

            db_model = model_to_create(
                **create.model_dump(exclude=set(create_columns - columns))
            )

            if not autocommit:
                self.__add_no_commit(db_model)
                return db_model
            else:
                self.__add_and_commit(db_model)
                return db_model

        except IntegrityError as e:
            print(e)
            raise HTTPException(
                status_code=403,
                detail=f"Cannot create {model_to_create.__qualname__}, \
                    possible duplicate or invalid attributes",
            )


    def get_model_or_404(
        self,
        model_to_get: Any,
        model_conditions: dict[str, Any] = {},
        order_by_column: str = "id",
        order: str = "asc",
        custom_error: str = "",
    ) -> Any:
        try:
            conditions: list[Any] = []
            for field_name in model_conditions:
                if model_conditions[field_name] is not None:
                    conditions.append(
                        and_(
                            getattr(model_to_get, field_name)
                            == model_conditions[field_name]
                        )
                    )

            if order != "asc":
                return (
                    self.db.query(model_to_get)
                    .filter(and_(*conditions))
                    .order_by(getattr(model_to_get, order_by_column).desc())
                    .one()
                )

            return self.db.query(model_to_get).filter(and_(*conditions)).one()

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_get.__qualname__}",
            )

        except Exception as e:
            print(e)
            if custom_error:
                raise HTTPException(404, detail=custom_error)

            raise HTTPException(404, detail=f"{model_to_get.__qualname__} not found")


    def update_model(
        self,
        model_to_update: Any,
        update: BaseModel,
        update_conditions: dict[str, Any] = {},
        autocommit: bool = True,
    ) -> Any:
        db_model = self.get_model_or_404(
            model_to_get=model_to_update, model_conditions=update_conditions
        )

        try:
            if not autocommit:
                self.__update_no_commit(db_model, update)
                return db_model
            else:
                self.__update_and_commit(db_model, update)
                return db_model

        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=403, detail=f"{model_to_update.__qualname__} update failed"
            )

    def list_model(
        self,
        model_to_list: Any,
        list_conditions: dict[str, Any] = {},
        date_range: DateRange | None = None,
        skip: int = 0,
        limit: int | None = 100,
        order_by_column: str = "id",
        order: str = "asc",
        count_by_column: str = "id",
        join_conditions: dict[Any, Any] = {},
        conjunction: str = "and",
    ) -> dict[str, Any]:
        if "limit" in list_conditions:
            limit = list_conditions["limit"]
            del list_conditions["limit"]

        if "skip" in list_conditions:
            skip = list_conditions["skip"]
            del list_conditions["skip"]

        if "order" in list_conditions:
            order = list_conditions["order"]
            del list_conditions["order"]

        limit = None if limit == 0 else limit
        try:
            conditions: list[Any] = self.__get_conditions(
                model_to_list, list_conditions, conjunction
            )

            conditions.extend(
                self.__get_join_conditions(model_to_list, join_conditions, conjunction)
            )

            join_models = [join_model for join_model in join_conditions]

            if date_range:
                conditions.append(
                    and_(
                        getattr(model_to_list, date_range.column_name)
                        >= date_range.from_date
                    )
                )
                conditions.append(
                    and_(
                        getattr(model_to_list, date_range.column_name)
                        <= date_range.to_date
                    )
                )

            try:
                db_model_count = int(
                    self.get_model_count(
                        model_to_list,
                        count_by_column,
                        list_conditions,
                        date_range,
                        join_conditions=join_conditions,
                        conjunction=conjunction,
                    )
                )

                querier = self.db.query(model_to_list)
                for join_model in join_models:
                    querier = querier.join(join_model)

                model_list = self.__make_query(
                    querier,
                    model_to_list,
                    conditions,
                    order_by_column,
                    order,
                    skip,
                    limit,
                    conjunction,
                )

            except Exception as e:
                print(e)
                db_model_count = 0
                model_list = []

            return {"items": model_list, "count": db_model_count}

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute for {model_to_list.__qualname__}",
            )

        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=404, detail=f"{model_to_list.__qualname__} not found"
            )


    def delete_model(
        self,
        model_to_delete: Any,
        delete_conditions: dict[str, Any] = {},
        autocommit: bool = True,
    ) -> dict[str, ActionStatus]:
        db_model = self.get_model_or_404(
            model_to_get=model_to_delete,
            model_conditions=delete_conditions,
        )
        try:
            if autocommit:
                self.__delete_and_commit(db_model)
                return {"status": ActionStatus.success}
            else:
                self.__delete_no_commit(db_model)
                return {"status": ActionStatus.success}

        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=403,
                detail=f"Cannot delete this {model_to_delete.__qualname__}, "
                + "check if it's still in use",
            )


    def get_model_count(
        self,
        model_to_count: Any,
        column_to_count_by: str,
        model_conditions: dict[str, Any] = {},
        date_range: DateRange | None = None,
        join_conditions: dict[Any, Any] = {},
        conjunction: str = "and",
    ) -> int:
        try:
            conditions: list[Any] = self.__get_conditions(
                model_to_count, model_conditions, conjunction
            )

            conditions.extend(
                self.__get_join_conditions(model_to_count, join_conditions, conjunction)
            )

            join_models = [join_model for join_model in join_conditions]

            if date_range:
                conditions.append(
                    and_(
                        getattr(model_to_count, date_range.column_name)
                        >= date_range.from_date
                    )
                )

                conditions.append(
                    and_(
                        getattr(model_to_count, date_range.column_name)
                        <= date_range.to_date
                    )
                )

            querier = self.db.query(
                func.count(getattr(model_to_count, column_to_count_by))
            )

            for join_model in join_models:
                querier = querier.join(join_model)

            if conditions:
                if conjunction == "or":
                    db_count = querier.filter(or_(false(), *conditions)).one()
                else:
                    db_count = querier.filter(and_(*conditions)).one()

            else:
                db_count = querier.one()

            db_count = db_count[0]

            if not db_count:
                return 0

            return int(db_count)

        except AttributeError:
            raise HTTPException(
                status_code=403,
                detail=f"Invalid attribute provided for {model_to_count.__qualname__}",
            )

        except Exception as e:
            print(e)
            raise HTTPException(
                status_code=404,
                detail=f"Could not retrieve count of {column_to_count_by}. \
                    Record not found",
            )

    def __add_and_commit(self, model_to_add: Any) -> None:
        # check if model to add is a list
        if isinstance(model_to_add, list):
            self.db.add_all(model_to_add)  # type: ignore
        else:
            self.db.add(model_to_add)
        self.db.commit()

    def __add_no_commit(self, model_to_add: Any) -> None:
        # check if model to add a list
        if isinstance(model_to_add, list):
            self.db.add_all(model_to_add)  # type: ignore
        else:
            self.db.add(model_to_add)

        self.db.flush()

    def __update_and_commit(self, model_to_update: Any, update: BaseModel) -> None:
        update_dict = self.__remove_invalid_fields(model_to_update, update)
        for key, value in update_dict.items():
            setattr(model_to_update, key, value)

        self.db.commit()
        self.db.refresh(model_to_update)

    def __update_no_commit(self, model_to_update: Any, update: BaseModel) -> None:
        update_dict = self.__remove_invalid_fields(model_to_update, update)

        for key, value in update_dict.items():
            setattr(model_to_update, key, value)

        self.db.flush()

    def __delete_and_commit(self, model_to_delete: Any) -> None:
        self.db.delete(model_to_delete)
        self.db.commit()

    def __delete_no_commit(self, model_to_delete: Any) -> None:
        self.db.delete(model_to_delete)
        self.db.flush()

    def __remove_invalid_fields(self, model: Any, data: BaseModel) -> dict[str, Any]:
        columns: set[str] = set(model.__table__.c.keys())
        data_fields: set[str] = set(data.model_dump(exclude_unset=True).keys())

        data_dict = data.model_dump(
            exclude=set(data_fields - columns),
            exclude_unset=True,
        )

        return data_dict

    def __get_conditions(
        self,
        model: Any,
        list_conditions: dict[str, Any],
        conjunction: str = "and",
    ) -> list[Any]:
        conditions: list[Any] = []
        for field_name in list_conditions:
            if list_conditions[field_name] is not None:
                if conjunction == "or":
                    conditions.append(
                        getattr(model, field_name) == list_conditions[field_name]
                    )
                else:
                    conditions.append(
                        and_(getattr(model, field_name) == list_conditions[field_name])
                    )
        return conditions

    def __get_join_conditions(
        self,
        model: Any,
        join_conditions: dict[Any, Any],
        conjunction: str = "and",
    ) -> list[Any]:
        join_models = [join_model for join_model in join_conditions]
        conditions: list[Any] = []
        for join_model in join_models:
            for field_name in join_conditions[join_model]:
                if join_conditions[join_model][field_name] is not None:
                    if conjunction == "or":
                        conditions.append(
                            getattr(join_model, field_name)
                            == join_conditions[join_model][field_name]
                        )
                    else:
                        conditions.append(
                            and_(
                                getattr(join_model, field_name)
                                == join_conditions[join_model][field_name]
                            )
                        )
        return conditions

    def __make_query(
        self,
        query: Any,
        model: Any,
        conditions: list[Any],
        order_by_column: str,
        order: str,
        skip: int,
        limit: int | None,
        conjunction: str,
    ) -> Any:
        if order != "asc":
            if conjunction == "or":
                return (
                    query.filter(or_(false(), *conditions))
                    .order_by(getattr(model, order_by_column).desc())
                    .offset(skip)
                    .limit(limit)
                    .all()
                )
            else:
                return (
                    query.filter(and_(*conditions))
                    .order_by(getattr(model, order_by_column).desc())
                    .offset(skip)
                    .limit(limit)
                    .all()
                )
        if conjunction == "or":
            return (
                query.filter(or_(false(), *conditions))
                .order_by(getattr(model, order_by_column))
                .offset(skip)
                .limit(limit)
                .all()
            )
        else:
            return query.filter(and_(*conditions)).offset(skip).limit(limit).all()
