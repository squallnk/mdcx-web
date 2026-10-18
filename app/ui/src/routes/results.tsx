import {
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Paper,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Typography,
} from "@mui/material";
import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { type ScrapeListEntry, type ScrapeShowData, useResultStore } from "@/store/resultStore";

export const Route = createFileRoute("/results")({
  component: ResultsComponent,
});

function Empty({ text }: { text: string }) {
  return (
    <Box sx={{ p: 4, textAlign: "center", color: "text.secondary" }}>
      <Typography variant="body2">{text}</Typography>
    </Box>
  );
}

function ResultTable({ entries, empty }: { entries: ScrapeListEntry[]; empty: string }) {
  if (entries.length === 0) return <Empty text={empty} />;

  return (
    <TableContainer component={Paper} elevation={0}>
      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>番号</TableCell>
            <TableCell>标题</TableCell>
            <TableCell>演员</TableCell>
            <TableCell>发行日期</TableCell>
            <TableCell>文件</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {entries.map((entry) => (
            <TableRow key={entry.id}>
              <TableCell sx={{ whiteSpace: "nowrap", fontWeight: 600 }}>
                {entry.real_number || entry.show_data?.data?.number || entry.show_data?.file_info?.number || "-"}
              </TableCell>
              <TableCell>{entry.show_data?.data?.title || entry.show_data?.show_name || "-"}</TableCell>
              <TableCell>{entry.show_data?.data?.actors?.join(", ") || "-"}</TableCell>
              <TableCell sx={{ whiteSpace: "nowrap" }}>{entry.show_data?.data?.release || "-"}</TableCell>
              <TableCell sx={{ wordBreak: "break-all" }}>
                {entry.show_data?.file_info?.file_path || entry.show_data?.file_info?.file_name || "-"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </TableContainer>
  );
}

function CurrentShowInfo({ showData }: { showData: ScrapeShowData | null }) {
  if (!showData) return <Empty text="等待 set_main_info 信号..." />;

  const info = showData.data ?? {};
  const file = showData.file_info ?? {};

  const fields: [string, string | undefined][] = [
    ["番号", info.number || file.number],
    ["标题", info.title || showData.show_name],
    ["原始标题", info.originaltitle],
    ["演员", info.actors?.join(", ")],
    ["导演", info.directors?.join(", ")],
    ["系列", info.series],
    ["制作商", info.studio],
    ["发行商", info.publisher],
    ["发行日期", info.release],
    ["片长", info.runtime],
    ["评分", info.score],
    ["马赛克", info.mosaic || file.mosaic],
    ["文件", file.file_path || file.file_name],
  ];
  const visibleFields = fields.filter((field): field is [string, string] => Boolean(field[1]));

  return (
    <Box sx={{ display: "flex", gap: 3, flexWrap: "wrap", p: 2 }}>
      {info.poster ? (
        <Box
          component="img"
          src={info.poster}
          alt={info.number ?? ""}
          sx={{
            width: 180,
            borderRadius: 2,
            border: "1px solid rgba(255,255,255,.08)",
            flexShrink: 0,
            alignSelf: "flex-start",
          }}
        />
      ) : null}

      <Box sx={{ flex: "1 1 320px", minWidth: 260 }}>
        {visibleFields.map(([label, value]) => (
          <Box key={label} sx={{ display: "flex", gap: 2, py: 0.5 }}>
            <Typography variant="body2" color="text.secondary" sx={{ minWidth: 80, flexShrink: 0 }}>
              {label}
            </Typography>
            <Typography variant="body2" sx={{ wordBreak: "break-word" }}>
              {value}
            </Typography>
          </Box>
        ))}

        {info.tags && info.tags.length > 0 ? (
          <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mt: 1.5 }}>
            {info.tags.map((tag) => (
              <Chip key={tag} label={tag} size="small" />
            ))}
          </Box>
        ) : null}

        {info.outline ? (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2, lineHeight: 1.7 }}>
            {info.outline}
          </Typography>
        ) : null}
      </Box>
    </Box>
  );
}

function ResultsComponent() {
  const [tab, setTab] = useState(0);
  const { success, failed, current, clearResults } = useResultStore();

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Box sx={{ display: "flex", alignItems: "center", justifyContent: "space-between", gap: 2, flexWrap: "wrap" }}>
        <Typography variant="h4">刮削结果</Typography>
        <Button variant="outlined" onClick={clearResults} disabled={success.length + failed.length === 0}>
          清空列表
        </Button>
      </Box>

      <Card>
        <Tabs value={tab} onChange={(_, value: number) => setTab(value)} sx={{ px: 2, borderBottom: 1, borderColor: "divider" }}>
          <Tab label={`成功 (${success.length})`} />
          <Tab label={`失败 (${failed.length})`} />
          <Tab label="当前番号" />
        </Tabs>
        <CardContent sx={{ p: tab === 2 ? 0 : 2 }}>
          {tab === 0 && <ResultTable entries={success} empty="还没有成功的刮削结果..." />}
          {tab === 1 && <ResultTable entries={failed} empty="还没有失败的刮削结果..." />}
          {tab === 2 && <CurrentShowInfo showData={current} />}
        </CardContent>
      </Card>
    </Box>
  );
}
