from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table


metadata = MetaData()
Project = Table('Project', metadata,
                Column('ProjectId', Integer, primary_key=True),
                Column('Name', String(100), nullable=False))

Document = Table('Document', metadata,
                 Column('DocumentId', Integer, primary_key=True),
                 Column('Name', String(100), nullable=False),
                 Column('Location', String(255), nullable=False),
                 Column('Description', String))

ProjectEntry = Table('ProjectEntry', metadata,
                     Column('ProjectId', None,
                            ForeignKey('Project.ProjectId')),
                     Column('DocumentId', None,
                            ForeignKey('Document.DocumentId')),
                     Column('AccessCount', Integer))
