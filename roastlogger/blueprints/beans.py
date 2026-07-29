"""Bean and label API routes."""

from __future__ import annotations

import os

from bson.objectid import ObjectId
from flask import Blueprint, current_app, jsonify, redirect, request, url_for

from models.bean_helpers import create_bean, update_bean
from roastlogger.database import get_beans_collection
from roastlogger.routing import register_unprefixed_routes
from roastlogger.time_utils import get_current_time_with_tz


blueprint = Blueprint("beans", __name__)


def api_beans_add():
    create_bean(get_beans_collection(), request.form.to_dict())
    return redirect(url_for("beans_list"))


def api_beans_edit(bean_id):
    update_bean(get_beans_collection(), bean_id, request.form.to_dict())
    return redirect(url_for("beans_list"))


def api_beans_delete(bean_id):
    get_beans_collection().update_one(
        {"_id": ObjectId(bean_id)},
        {"$set": {"archived": True, "updated_at": get_current_time_with_tz()}},
    )
    return redirect(url_for("beans_list"))


def api_label_images():
    image_directory = os.path.join(current_app.static_folder, "img")
    images = []
    if os.path.isdir(image_directory):
        for filename in sorted(os.listdir(image_directory)):
            if filename.lower().endswith(
                (".png", ".jpg", ".jpeg", ".webp", ".svg")
            ):
                images.append(filename)
    return jsonify({"images": images})


def api_beans_label(bean_id):
    bean = get_beans_collection().find_one(
        {"_id": ObjectId(bean_id), "archived": {"$ne": True}}
    )
    if not bean:
        return jsonify({"success": False, "error": "Bean not found"}), 404
    data = request.get_json()
    label_data = {
        "name": data.get("name", ""),
        "origin": data.get("origin", ""),
        "process": data.get("process", ""),
        "roastLevel": data.get("roastLevel", ""),
        "flavorNotes": data.get("flavorNotes", ""),
        "roastDate": data.get("roastDate", ""),
        "accentColor": data.get("accentColor", ""),
        "templateId": data.get("templateId", "nova"),
        "fontPreset": data.get("fontPreset", "modern"),
        "aspectRatio": data.get("aspectRatio", "5:4"),
        "imageSrc": data.get("imageSrc", ""),
        "exportWidthCm": data.get("exportWidthCm", 10),
        "exportHeightCm": data.get("exportHeightCm", 8),
    }
    get_beans_collection().update_one(
        {"_id": ObjectId(bean_id)},
        {"$set": {"label": label_data, "updated_at": get_current_time_with_tz()}},
    )
    return jsonify({"success": True})


def api_label_preferences():
    most_recent = get_beans_collection().find_one(
        {"archived": {"$ne": True}, "label.templateId": {"$exists": True}},
        sort=[("updated_at", -1)],
    )
    label = (most_recent or {}).get("label") or {}
    return jsonify(
        {
            "templateId": label.get("templateId", "nova"),
            "fontPreset": label.get("fontPreset", "modern"),
            "aspectRatio": label.get("aspectRatio", "5:4"),
        }
    )


register_unprefixed_routes(
    blueprint,
    [
        ("/api/beans/add", "api_beans_add", api_beans_add, ["POST"]),
        (
            "/api/beans/edit/<bean_id>",
            "api_beans_edit",
            api_beans_edit,
            ["POST"],
        ),
        (
            "/api/beans/delete/<bean_id>",
            "api_beans_delete",
            api_beans_delete,
            ["POST"],
        ),
        ("/api/label/images", "api_label_images", api_label_images, ["GET"]),
        (
            "/api/beans/<bean_id>/label",
            "api_beans_label",
            api_beans_label,
            ["POST"],
        ),
        (
            "/api/label/preferences",
            "api_label_preferences",
            api_label_preferences,
            ["GET"],
        ),
    ],
)
