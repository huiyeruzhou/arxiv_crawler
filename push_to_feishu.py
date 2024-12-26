import requests
import json
from rich.console import Console
import pandas as pd
import os
import datetime as dt


class Push2Feishu(object):
    def __init__(self, app_id, app_secret, personal_cfg='personal_cfg.json', retry=3):
        """
        飞书机器人创建及获取 app_id, app_secret 参见：
        https://open.feishu.cn/document/home/develop-a-bot-in-5-minutes/create-an-app
        """
        self.app_id = app_id
        self.app_secret = app_secret
        self.retry = retry
        self.personal_cfg_fname = personal_cfg
        self.personal_cfg = (
            {}
            if not os.path.exists(self.personal_cfg_fname)
            else json.load(open(self.personal_cfg_fname))
        )
        self.console = Console()
        self.token = self.update_tenant_access_token()
        self.table_fields = json.loads(
            '''[
  {
    "field_name": "Title",
    "is_primary": true,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  },
  {
    "field_name": "Interest",
    "is_primary": false,
    "property": {
      "options": [
        {
          "color": 10,
          "name": "chosen"
        },
        {
          "color": 33,
          "name": "CORE"
        },
        {
          "color": 12,
          "name": "PEER"
        },
        {
          "color": 13,
          "name": "RELATED"
        },
        {
          "color": 15,
          "name": "INTERESTING"
        },
        {
          "color": 2,
          "name": "NORMAL"
        },
        {
          "color": 0,
          "name": "IRRELEVANT"
        },
        {
          "color": 43,
          "name": "filtered"
        }
      ]
    },
    "type": 3,
    "ui_type": "SingleSelect"
  },
  {
    "field_name": "Title Translated",
    "is_primary": false,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  },
  {
    "field_name": "Categories",
    "is_primary": false,
    "property": {
      "options": [
        {
          "color": 0,
          "name": "cs.CL"
        },
        {
          "color": 1,
          "name": "cs.AI"
        },
        {
          "color": 2,
          "name": "econ.GN"
        },
        {
          "color": 3,
          "name": "cs.CV"
        },
        {
          "color": 4,
          "name": "cs.MM"
        },
        {
          "color": 5,
          "name": "cs.SE"
        },
        {
          "color": 6,
          "name": "cs.LG"
        },
        {
          "color": 7,
          "name": "cs.CY"
        },
        {
          "color": 8,
          "name": "cs.CR"
        },
        {
          "color": 9,
          "name": "cs.GR"
        },
        {
          "color": 0,
          "name": "cs.IR"
        },
        {
          "color": 1,
          "name": "cs.HC"
        },
        {
          "color": 2,
          "name": "physics.chem-ph"
        },
        {
          "color": 3,
          "name": "q-bio.BM"
        },
        {
          "color": 4,
          "name": "cs.RO"
        },
        {
          "color": 5,
          "name": "eess.SP"
        },
        {
          "color": 6,
          "name": "cs.SD"
        },
        {
          "color": 7,
          "name": "eess.AS"
        },
        {
          "color": 8,
          "name": "cs.DC"
        },
        {
          "color": 9,
          "name": "cs.PL"
        },
        {
          "color": 0,
          "name": "cs.MA"
        },
        {
          "color": 1,
          "name": "cs.NE"
        },
        {
          "color": 2,
          "name": "cs.SI"
        },
        {
          "color": 1,
          "name": "Categories"
        },
        {
          "color": 2,
          "name": "cs.AR"
        },
        {
          "color": 3,
          "name": "cs.DB"
        },
        {
          "color": 4,
          "name": "cs.LO"
        },
        {
          "color": 5,
          "name": "cs.CE"
        },
        {
          "color": 6,
          "name": "cs.IT"
        },
        {
          "color": 7,
          "name": "math.OC"
        },
        {
          "color": 8,
          "name": "stat.ML"
        },
        {
          "color": 9,
          "name": "q-bio.NC"
        },
        {
          "color": 10,
          "name": "physics.comp-ph"
        },
        {
          "color": 0,
          "name": "cond-mat.mtrl-sci"
        },
        {
          "color": 1,
          "name": "q-fin.CP"
        },
        {
          "color": 2,
          "name": "cs.ET"
        },
        {
          "color": 3,
          "name": "cs.SC"
        },
        {
          "color": 4,
          "name": "q-bio.QM"
        },
        {
          "color": 5,
          "name": "stat.ME"
        },
        {
          "color": 6,
          "name": "cond-mat.dis-nn"
        },
        {
          "color": 7,
          "name": "physics.data-an"
        },
        {
          "color": 8,
          "name": "math.NA"
        },
        {
          "color": 9,
          "name": "math.PR"
        },
        {
          "color": 10,
          "name": "astro-ph.IM"
        },
        {
          "color": 0,
          "name": "cs.NI"
        }
      ]
    },
    "type": 4,
    "ui_type": "MultiSelect"
  },
  {
    "field_name": "Authors",
    "is_primary": false,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  },
  {
    "field_name": "Arxiv",
    "is_primary": false,
    "property": null,
    "type": 15,
    "ui_type": "Url"
  },
  {
    "field_name": "PapersCool",
    "is_primary": false,
    "property": null,
    "type": 15,
    "ui_type": "Url"
  },
  {
    "field_name": "First Submitted Date",
    "is_primary": false,
    "property": {
      "auto_fill": false,
      "date_formatter": "yyyy/MM/dd"
    },
    "type": 5,
    "ui_type": "DateTime"
  },
  {
    "field_name": "First Announced Date",
    "is_primary": false,
    "property": {
      "auto_fill": false,
      "date_formatter": "yyyy/MM/dd"
    },
    "type": 5,
    "ui_type": "DateTime"
  },
  {
    "field_name": "Abstract",
    "is_primary": false,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  },
  {
    "field_name": "Abstract Translated",
    "is_primary": false,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  },
  {
    "field_name": "Comments",
    "is_primary": false,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  },
  {
    "field_name": "Note",
    "is_primary": false,
    "property": null,
    "type": 1,
    "ui_type": "Text"
  }
]'''
        )

    def update_tenant_access_token(self):
        """
        获取 tenant_access_token，此数据每30分钟更新一次。为避免失效导致的错误，
        最好每次请求前都调用此方法获取最新的 token。
        """

        url = 'https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal'
        headers = {'Content-Type': 'application/json; charset=utf-8'}
        data = json.dumps({'app_id': self.app_id, 'app_secret': self.app_secret})
        error = 0
        # 重试机制
        while error < self.retry:
            try:
                response = requests.post(url, headers=headers, data=data)
                result = response.json()
                if result.get('code') != 0:
                    error += 1
                    self.console.log(
                        f'[bold red]Request tenant_access_token failed: {result.get("msg")}'
                    )
                    self.console.print_exception()
                    self.console.log(
                        f'[bold red]Retrying update_tenant_access_token... {error}/{self.retry}'
                    )
                else:
                    self.token = result.get('tenant_access_token')
                    return self.token
            except Exception as e:
                error += 1
                self.console.log(
                    f'[bold red]Request tenant_access_token failed: {str(e)}'
                )
                self.console.print_exception()
                self.console.log(
                    f'[bold red]Retrying update_tenant_access_token... {error}/{self.retry}'
                )

    def create_bitable(self, bitable_name, time_zone='Asia/Shanghai'):
        """
        创建飞书表格。
        Ref. https://open.feishu.cn/document/server-docs/docs/bitable-v1/app/create
        """

        self.update_tenant_access_token()
        url = 'https://open.feishu.cn/open-apis/bitable/v1/apps'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {self.token}',
        }
        data = json.dumps(
            {'name': bitable_name, 'folder_token': '', 'time_zone': time_zone}
        )
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(
                    f'[bold red]Create bitable failed: {result.get("msg")}'
                )
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]Create bitable failed: {str(e)}')
            self.console.print_exception()
        return None

    def transfer_owner(self, app_token, new_owner_userid):
        """
        转让表格的所有权。
        飞书应用直接为用户创建文件需要使用 user_access_token，而获取 user_access_token
        需要配置重定向域名，过于繁琐。这里使用应用创建多维表格，然后将所有权转让给
        指定用户。
        """
        self.update_tenant_access_token()
        url = f'https://open.feishu.cn/open-apis/drive/v1/permissions/{app_token}/members/transfer_owner?type=bitable&remove_old_owner=false'
        headers = {
            'Content-Type': 'application/json; charset=utf-8',
            'Authorization': f'Bearer {self.token}',
        }
        data = json.dumps({'member_type': 'userid', "member_id": new_owner_userid})
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(
                    f'[bold red]Transfer owner failed: {result.get("msg")}'
                )
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]Transfer owner failed: {str(e)}')
            self.console.print_exception()

        return None

    def create_kanban(self, app_token, table_id, kanban_name='看板'):
        '''此函数用于创建 Bitable 中的看板
        Ref. https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-view/create
        '''

        self.update_tenant_access_token()
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/views'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        data = json.dumps({'view_name': kanban_name, 'view_type': 'kanban'})
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(f'[bold red]Create kanban failed: {result.get("msg")}')
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]Create kanban failed: {str(e)}')
            self.console.print_exception()

        return None

    def create_table(self, app_token, table_name):
        '''此函数用于创建 Bitable 中的表格
        Ref. https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/create
        '''
        self.update_tenant_access_token()
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        data = json.dumps(
            {
                'table': {
                    'name': f'{table_name}',
                    'default_view_name': '表格',
                    'fields': self.table_fields,
                }
            }
        )
        try:
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(f'[bold red]Create table failed: {result.get("msg")}')
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]Create table failed: {str(e)}')
            self.console.print_exception()

        return None

    def delete_table(self, app_token, table_id):
        '''此函数用于删除 Bitable 中的文件
        Ref. https://open.feishu.cn/document/server-docs/docs/drive-v1/file/delete
        '''
        self.update_tenant_access_token()
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        try:
            response = requests.delete(url, headers=headers)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(f'[bold red]Delete table failed: {result.get("msg")}')
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]Delete table failed: {str(e)}')
            self.console.print_exception()

    def list_bitable_tables(self, app_token):
        '''此函数用于列出 Bitable 中的表格
        Ref. https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/list
        '''
        self.update_tenant_access_token()
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables?page_size=100'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        try:
            response = requests.get(url, headers=headers)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(f'[bold red]List table failed: {result.get("msg")}')
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]List table failed: {str(e)}')
            self.console.print_exception()

        return None

    @staticmethod
    def format_data(csv_name, include_filtered=False):
        '''
        此函数用于将 CSV 数据转换为 Bitable 表格可以接受的 json 数据
        '''
        content = pd.read_csv(
            csv_name,
            encoding='utf-8',
            header=None,
            names=[
                'Title',
                'Interest',
                'Title Translated',
                'Categories',
                'Authors',
                'Arxiv',
                'PapersCool',
                'First Submitted Date',
                'First Announced Date',
                'Abstract',
                'Abstract Translated',
                'Comments',
                'Note',
            ],
            sep='\t',
        )
        chosen_content = (
            content[content['Interest'] == 'chosen']
            if not include_filtered
            else content
        )
        if len(chosen_content) == 0:
            return None
        # 格式化时间
        chosen_content.loc[:, 'First Submitted Date'] = pd.to_datetime(
            chosen_content['First Submitted Date'], format='%Y-%m-%d'
        )
        chosen_content.loc[:, 'First Announced Date'] = pd.to_datetime(
            chosen_content['First Announced Date'], format='%Y-%m-%d'
        )
        json_data = json.loads(
            chosen_content.to_json(orient='records', force_ascii=False, indent=2)
        )
        for record in json_data:
            if 'Categories' in record:
                record['Categories'] = record['Categories'].split(',')
            if 'Arxiv' in record:
                record['Arxiv'] = {'link': record['Arxiv'], 'text': record['Arxiv']}
            if 'PapersCool' in record:
                record['PapersCool'] = {
                    'link': record['PapersCool'],
                    'text': record['PapersCool'],
                }

        data = []
        for record in json_data:
            data.append({'fields': record})
        return json.dumps({'records': data}, ensure_ascii=False).encode('utf-8')

    def post_data(self, app_token, table_id, json_data):
        '''此函数用于向 Bitable 中的表格推送数据
        Ref. https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-data/create
        '''
        self.update_tenant_access_token()
        url = f'https://open.feishu.cn/open-apis/bitable/v1/apps/{app_token}/tables/{table_id}/records/batch_create'
        headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json; charset=utf-8',
        }
        try:
            response = requests.post(url, headers=headers, data=json_data)
            result = response.json()
            if result.get('code') != 0:
                self.console.log(f'[bold red]Push data failed: {result.get("msg")}')
                self.console.print_exception()
            else:
                return result
        except Exception as e:
            self.console.log(f'[bold red]Push data failed: {str(e)}')
            self.console.print_exception()

        return None

    def to_feishu(self, csv_name, userid, include_filtered=False):
        '''此函数用于读取 CSV 数据，判断是否存在多维表格并推送到多维表格之中'''
        csv_basename = os.path.basename(csv_name)
        basename = os.path.splitext(csv_basename)[0]
        year, month, day = basename.split('-')

        # format data
        data = self.format_data(csv_name, include_filtered)
        if data is None:
            self.console.log(f'[bold red]No data to push to Feishu')
            return

        if userid not in self.personal_cfg or year not in self.personal_cfg.get(userid):
            bitable_create_reponse = self.create_bitable(f'arXiv-文献库-{year}')
            bitable_token = (
                bitable_create_reponse.get('data').get('app').get('app_token')
            )
            default_table_id = (
                bitable_create_reponse.get('data').get('app').get('default_table_id')
            )
            # 转让多维表格所有权
            self.transfer_owner(bitable_token, userid)
            # 创建当前月份的数据表
            create_table = self.create_table(bitable_token, month)
            table_id = create_table.get('data').get('table_id')
            self.create_kanban(bitable_token, table_id)
            self.delete_table(bitable_token, default_table_id)
            # Update personal_cfg
            self.personal_cfg[userid] = {
                year: {
                    'bitable_token': bitable_token,
                    "tables_id": {month: table_id},
                }
            }

            with open(self.personal_cfg_fname, 'w') as f:
                json.dump(self.personal_cfg, f, indent=2, ensure_ascii=False)
        else:
            bitable_token = self.personal_cfg.get(userid).get(year).get('bitable_token')
            tables = self.list_bitable_tables(bitable_token)
            # 获取表格 ID
            table_id = None
            if tables:
                for item in tables.get('data').get('items'):
                    if item.get('name') == month:
                        table_id = item.get('table_id')
                        break
            if not table_id:
                create_table = self.create_table(bitable_token, month)
                if create_table:
                    table_id = create_table.get('data').get('table_id')
                    self.create_kanban(bitable_token, table_id)
            # Update personal_cfg
            self.personal_cfg[userid][year]['tables_id'][month] = table_id
            with open(self.personal_cfg_fname, 'w') as f:
                json.dump(self.personal_cfg, f, indent=2, ensure_ascii=False)

        self.post_data(bitable_token, table_id, data)
        self.console.log(f'[bold green]Push data to Feishu success')
