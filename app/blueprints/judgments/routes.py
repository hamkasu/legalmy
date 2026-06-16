from flask import Blueprint, render_template, jsonify, request, abort
from sqlalchemy import text
from app.models.judgment import Judgment, Citation, OutcomeType, CitationRelationship
from app.extensions import db
from flask_login import login_required

bp = Blueprint('judgments', __name__)


@bp.route('/<judgment_id>/graph')
@login_required
def graph_view(judgment_id):
    """Judgment detail page with embedded citation graph visualization."""
    judgment = Judgment.query.filter_by(id=judgment_id).first()
    if not judgment:
        abort(404)

    return render_template('judgments/graph.html', judgment=judgment)


@bp.route('/api/citations/<judgment_id>/graph')
@login_required
def graph_api(judgment_id):
    """API endpoint returning citation graph data with recursive traversal."""
    depth = request.args.get('depth', 1, type=int)
    if depth < 1 or depth > 3:
        depth = 1

    judgment = Judgment.query.filter_by(id=judgment_id).first()
    if not judgment:
        return jsonify({'error': 'Judgment not found'}), 404

    # Recursive CTE to traverse citation graph
    query = text("""
        WITH RECURSIVE citation_graph AS (
            -- Base: direct citations to/from focal judgment
            SELECT
                c.citing_judgment_id,
                c.cited_judgment_id,
                c.relationship,
                1 AS depth
            FROM citations c
            WHERE c.citing_judgment_id = :focal_id OR c.cited_judgment_id = :focal_id

            UNION ALL

            -- Recursive: expand one hop further
            SELECT
                c.citing_judgment_id,
                c.cited_judgment_id,
                c.relationship,
                cg.depth + 1
            FROM citations c
            JOIN citation_graph cg ON (
                c.citing_judgment_id = cg.cited_judgment_id OR
                c.cited_judgment_id = cg.citing_judgment_id
            )
            WHERE cg.depth < :max_depth
        )
        SELECT DISTINCT
            judgment_id,
            citation,
            title,
            court_level,
            date_decided,
            outcome,
            (
                SELECT COUNT(*) FROM citations
                WHERE cited_judgment_id = j.id
            ) AS citation_count
        FROM (
            SELECT DISTINCT j.id as judgment_id, j.citation, j.title, j.court_level, j.date_decided, j.outcome
            FROM citation_graph cg
            JOIN judgments j ON (j.id = cg.citing_judgment_id OR j.id = cg.cited_judgment_id)
            WHERE j.is_published = true
        ) AS j
        ORDER BY j.id
    """)

    result = db.session.execute(
        query,
        {'focal_id': judgment_id, 'max_depth': depth}
    )

    nodes = []
    node_ids = set()

    for row in result:
        if row.judgment_id not in node_ids:
            node_ids.add(row.judgment_id)
            # Determine node color based on outcome
            if row.outcome == OutcomeType.ALLOWED:
                color = '#16A34A'  # green
            elif row.outcome == OutcomeType.DISMISSED:
                color = '#DC2626'  # red
            else:
                color = '#9CA3AF'  # grey

            # Focal node has gold ring
            is_focal = row.judgment_id == judgment_id

            nodes.append({
                'id': row.judgment_id,
                'label': row.citation,
                'title': row.title,
                'court': row.court_level.value if row.court_level else 'Unknown',
                'year': row.date_decided.year if row.date_decided else None,
                'outcome': row.outcome.value if row.outcome else None,
                'color': '#B8973A' if is_focal else color,
                'radius': 25 if is_focal else 15 + (min(row.citation_count, 10) * 1.5),
                'is_focal': is_focal,
                'citation_count': row.citation_count
            })

    # Fetch edges with relationship info
    edges_query = text("""
        WITH RECURSIVE citation_graph AS (
            SELECT
                c.citing_judgment_id,
                c.cited_judgment_id,
                c.relationship,
                1 AS depth
            FROM citations c
            WHERE c.citing_judgment_id = :focal_id OR c.cited_judgment_id = :focal_id

            UNION ALL

            SELECT
                c.citing_judgment_id,
                c.cited_judgment_id,
                c.relationship,
                cg.depth + 1
            FROM citations c
            JOIN citation_graph cg ON (
                c.citing_judgment_id = cg.cited_judgment_id OR
                c.cited_judgment_id = cg.citing_judgment_id
            )
            WHERE cg.depth < :max_depth
        )
        SELECT DISTINCT
            citing_judgment_id,
            cited_judgment_id,
            relationship
        FROM citation_graph
        WHERE citing_judgment_id IN (
            SELECT judgment_id FROM (
                SELECT j.id as judgment_id
                FROM citation_graph cg
                JOIN judgments j ON (j.id = cg.citing_judgment_id OR j.id = cg.cited_judgment_id)
            ) sub
        )
        AND cited_judgment_id IN (
            SELECT judgment_id FROM (
                SELECT j.id as judgment_id
                FROM citation_graph cg
                JOIN judgments j ON (j.id = cg.citing_judgment_id OR j.id = cg.cited_judgment_id)
            ) sub
        )
    """)

    edge_result = db.session.execute(
        edges_query,
        {'focal_id': judgment_id, 'max_depth': depth}
    )

    edges = []
    relationship_colors = {
        CitationRelationship.FOLLOWED: '#16A34A',      # green
        CitationRelationship.DISTINGUISHED: '#F97316',  # orange
        CitationRelationship.OVERRULED: '#DC2626',      # red
        CitationRelationship.CONSIDERED: '#3B82F6',     # blue
        CitationRelationship.REFERRED: '#6366F1',       # indigo
        CitationRelationship.APPROVED: '#10B981',       # emerald
    }

    for row in edge_result:
        relationship_enum = CitationRelationship(row.relationship)
        edges.append({
            'source': row.citing_judgment_id,
            'target': row.cited_judgment_id,
            'relationship': relationship_enum.value,
            'color': relationship_colors.get(relationship_enum, '#9CA3AF')
        })

    return jsonify({
        'nodes': nodes,
        'edges': edges,
        'depth': depth,
        'focal_id': judgment_id
    })
