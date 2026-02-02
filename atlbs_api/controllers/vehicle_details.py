# -*- coding: utf-8 -*-

import os
from passlib.context import CryptContext
from odoo.api import Environment
from odoo import http, tools, _
from odoo import api, fields, models, _
from odoo.http import request, Response
from odoo import SUPERUSER_ID
from odoo import registry as registry_get
from itertools import groupby
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
import json
import pytz
import re
import time
import base64
from odoo.addons.atlbs_api.controllers.db_config import GetDBName

# {
#     "car_id": "CAR001",
#     "title_en": "Toyota Corolla 2022",
#     "vin_sn": "VIN1234567890"
# }
from odoo.http import request
from odoo.api import Environment


class VehicleDetails(http.Controller):
    print(" VehicleAPI controller LOADED")


# code added on february 02 for security
    @http.route(['/vehicle/create'], type='http', auth='none', methods=['POST'], csrf=False)
    def create_vehicle(self, **kwargs):
        try:
            # 🔹 Check API Key in headers
            api_key = request.httprequest.headers.get('X-API-KEY')
            if api_key != '9e7ba5v1-66af-4363-85a5-2a258fe16be1':
                return Response(
                    json.dumps({
                        'status': 'failed',
                        'message': 'Unauthorized: Invalid API Key',
                        'response': {}
                    }),
                    status=401,
                    content_type='application/json'
                )

            # 🔹 JSON body
            data = request.httprequest.get_json(force=True)
            required_fields = ['car_id', 'title_en', 'vin_sn']
            for field in required_fields:
                if not data.get(field):
                    return Response(
                        json.dumps({
                            'status': 'failed',
                            'message': f'{field} is required',
                            'response': {}
                        }),
                        status=400,
                        content_type='application/json'
                    )

            env = request.env

            # Check duplicate VIN
            existing_vehicle = env['vehicle.details'].sudo().search([('vin_sn', '=', data['vin_sn'])], limit=1)
            if existing_vehicle:
                return Response(
                    json.dumps({
                        'status': 'failed',
                        'message': 'Vehicle with this VIN already exists',
                        'response': {'vehicle_id': existing_vehicle.id}
                    }),
                    status=409,
                    content_type='application/json'
                )

            # Create vehicle
            vehicle = env['vehicle.details'].sudo().create({
                'car_id': data['car_id'],
                'title_en': data['title_en'],
                'vin_sn': data['vin_sn'],
            })

            return Response(
                json.dumps({
                    'status': 'success',
                    'message': 'Vehicle created successfully',
                    'response': {
                        'vehicle_id': vehicle.id,
                        'car_id': vehicle.car_id,
                        'title_en': vehicle.title_en,
                        'vin_sn': vehicle.vin_sn,
                    }
                }),
                status=201,
                content_type='application/json'
            )

        except Exception as e:
            return Response(
                json.dumps({
                    'status': 'error',
                    'message': str(e),
                    'response': {}
                }),
                status=500,
                content_type='application/json'
            )



# code commented because we are not providing autherization key
    # @http.route('/vehicle/create', type='http', auth='public', methods=['POST'], csrf=False)
    # def create_vehicle(self, **kwargs):
    #     try:
    #         # JSON body
    #         data = request.httprequest.get_json(force=True)
    #
    #         required_fields = ['car_id', 'title_en', 'vin_sn']
    #
    #         for field in required_fields:
    #             if not data.get(field):
    #                 return Response(
    #                     json.dumps({
    #                         'status': 'failed',
    #                         'message': f'{field} is required',
    #                         'response': {}
    #                     }),
    #                     status=400,
    #                     content_type='application/json'
    #                 )
    #
    #         env = request.env
    #
    #         # Check duplicate VIN
    #         existing_vehicle = env['vehicle.details'].sudo().search(
    #             [('vin_sn', '=', data['vin_sn'])], limit=1
    #         )
    #
    #         if existing_vehicle:
    #             return Response(
    #                 json.dumps({
    #                     'status': 'failed',
    #                     'message': 'Vehicle with this VIN already exists',
    #                     'response': {
    #                         'vehicle_id': existing_vehicle.id
    #                     }
    #                 }),
    #                 status=409,
    #                 content_type='application/json'
    #             )
    #
    #         # Create vehicle
    #         vehicle = env['vehicle.details'].sudo().create({
    #             'car_id': data['car_id'],
    #             'title_en': data['title_en'],
    #             'vin_sn': data['vin_sn'],
    #         })
    #
    #         return Response(
    #             json.dumps({
    #                 'status': 'success',
    #                 'message': 'Vehicle created successfully',
    #                 'response': {
    #                     'vehicle_id': vehicle.id,
    #                     'car_id': vehicle.car_id,
    #                     'title_en': vehicle.title_en,
    #                     'vin_sn': vehicle.vin_sn,
    #                 }
    #             }),
    #             status=201,
    #             content_type='application/json'
    #         )
    #
    #     except Exception as e:
    #
    #         return Response(
    #             json.dumps({
    #                 'status': 'error',
    #                 'message': str(e),
    #                 'response': {}
    #             }),
    #             status=500,
    #             content_type='application/json'
    #         )

